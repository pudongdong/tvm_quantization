from __future__ import absolute_import, print_function


from collections import namedtuple
import argparse, json, os, requests, sys, time
from io import BytesIO
from os.path import join, isfile
from PIL import Image

import numpy as np
from matplotlib import pyplot as plt

from collections import namedtuple
import tvm
from tvm import relay
from tvm.contrib import download
from tvm import autotvm
from tvm.autotvm.tuner import XGBTuner, GATuner, RandomTuner, GridSearchTuner
from tvm.contrib.util import tempdir

import mxnet as mx
from mxnet import gluon
import logging
import os
import time

import logging
logging.basicConfig(level=logging.DEBUG)

from tvm.contrib.debugger import debug_runtime as graph_runtime


# # Tensorflow imports
# import tensorflow as tf

# # Tensorflow utility functions
# import tvm.relay.testing.tf as tf_testing

# import tensorflow as tf
# try:
#     tf_compat_v1 = tf.compat.v1
# except ImportError:
#     tf_compat_v1 = tf


Config = namedtuple('Config', ['model', 'nbit_input',  'dtype_input', 'nbit_output', 'dtype_output', 'global_scale', 'batch_size'])

# Set number of threads used for tuning based on the number of
# physical CPU cores on your machine.
# num_threads = 2
# os.environ["TVM_NUM_THREADS"] = str(num_threads)

def get_mxnet_model(model_name, batch_size):
    """Get mxnet model.

    Parameters
    ----------
    model_name : str
    batch_size : num

    Returns
    -------
    mod : tvm.relay.Module
    params : dict of str to tvm.NDArray
    input_shape : tuple

    """

    gluon_model = gluon.model_zoo.vision.get_model(model_name, pretrained=True)

    img_path='/home/terse/code/programming/blog/TVM_quantization/tf/elephant-299.jpg'
    from PIL import Image
    image = Image.open(img_path).resize((299, 299))
    x = np.array(image).reshape(1,3,299,299)
    start_time = time.time()
    y = gluon_model(mx.ndarray.array(x))
    print("=======", (time.time()-start_time)*1000)
    
    img_size = 299 if model_name == 'inceptionv3' else 224
    input_shape = (batch_size, 3, img_size, img_size)
    mod, params = relay.frontend.from_mxnet(gluon_model, {"data": input_shape})

    return mod,params,input_shape


def quantize_relay_module(mod, params, qconfig=None):
    """ Quantize the relay module with qconfig options.

    Parameters:
    ------
    mod : tvm.relay.module
        The original module.

    qconfig : tvm.relay.quantize.quantize.QConfig
        The quantization configuration

    Returns:
    ------
    qfunc : vm.relay.expr.Function
        The graph after quantization
    
    """

    # default qconfig
    if not qconfig:
        qconfig = tvm.relay.quantize.qconfig()

    with qconfig:
        logging.debug('current quantize config')
        logging.debug(tvm.relay.quantize.current_qconfig())
        
        mod = tvm.relay.quantize.quantize(mod,params=params)

        logging.debug('after quantize')
        logging.debug(mod['main'].astext(show_meta_data=False))
    return mod


def autotvm_tune(func,params,target):
    """

    Parameters:
    ----------
    func : relay.expr.Function
    params : dict of str to numpy array
    target : tvm.target.Target
    ops : List of relay.op

    """

    # Array of autotvm.task.Task
    tasks = autotvm.task.extract_from_program(func, target=target,
                                            params=params, ops=(relay.op.nn.conv2d,))
    # Check tasks.
    for i in range(len(tasks)):
        op_name = tasks[i].workload[0]
        if op_name == 'conv2d':
            func_create = 'topi_x86_conv2d_NCHWc'
        elif op_name == 'depthwise_conv2d_nchw':
            func_create = 'topi_x86_depthwise_conv2d_NCHWc_from_nchw'
        else:
            raise ValueError("Tuning {} is not supported on x86".format(op_name))

        print ( "[Create Task %2d/%2d (%s, %s) ] " % (i+1, len(tasks), tasks[i].name, tasks[i].workload[0]))

        tsk = autotvm.task.create(func_create, args=tasks[i].args,
                                    target=tasks[i].target, template_key='direct')
        tsk.workload = tasks[i].workload
        tasks[i] = tsk


    # turning option.
    tuner='xgb'
    n_trial=100
    early_stopping=None
    log_filename='tuning.log'
    use_transfer_learning=True
    measure_option = autotvm.measure_option(
                builder=autotvm.LocalBuilder(timeout=10),
                runner=autotvm.LocalRunner(number=10, repeat=1, min_repeat_ms=1000))


    # create tmp log file
    tmp_log_file = log_filename + ".tmp"
    if os.path.exists(tmp_log_file):
        os.remove(tmp_log_file)

    for i, tsk in enumerate(reversed(tasks)):
        prefix = "[Task %2d/%2d] " %(i+1, len(tasks))

        # create tuner
        if tuner == 'xgb' or tuner == 'xgb-rank':
            tuner_obj = XGBTuner(tsk, loss_type='rank')
        elif tuner == 'ga':
            tuner_obj = GATuner(tsk, pop_size=100)
        elif tuner == 'random':
            tuner_obj = RandomTuner(tsk)
        elif tuner == 'gridsearch':
            tuner_obj = GridSearchTuner(tsk)
        else:
            raise ValueError("Invalid tuner: " + tuner)

        if use_transfer_learning:
            if os.path.isfile(tmp_log_file):
                tuner_obj.load_history(autotvm.record.load_from_file(tmp_log_file))

        # do tuning
        tuner_obj.tune(n_trial=min(n_trial, len(tsk.config_space)),
                       early_stopping=early_stopping,
                       measure_option=measure_option,
                       callbacks=[
                           autotvm.callback.progress_bar(n_trial, prefix=prefix),
                           autotvm.callback.log_to_file(tmp_log_file)])

    # pick best records to a cache file
    autotvm.record.pick_best(tmp_log_file, log_filename)
    os.remove(tmp_log_file)



def build_module(mod,params,target,best_records=None):

    # build module
    if best_records:
        with autotvm.apply_history_best(best_records):
            with relay.build_config(opt_level=3):
                graph, lib, params = relay.build_module.build(mod, target=target, params=params)
    else:
        with relay.build_config(opt_level=3):
            graph, lib, params = relay.build_module.build(mod, target=target, params=params)

    return graph,lib,params


def save_compiled_module(graph,lib,params,dir_path):

    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    lib_file = os.path.join(dir_path,"lib.tar")
    graph_file = os.path.join(dir_path,'graph.json')
    params_file = os.path.join(dir_path,'param.params')

    lib.export_library(lib_file)
    with open(graph_file,"w") as fo:
        fo.write(graph)
    with open(params_file,"wb") as fo:
        fo.write(relay.save_param_dict(params))


def load_module(dir_path,ctx=None,debug=False):


    lib_file = os.path.join(dir_path,"lib.tar")
    graph_file = os.path.join(dir_path,'graph.json')
    params_file = os.path.join(dir_path,'param.params')

    lib = tvm.module.load(lib_file)
    graph = open(graph_file).read()
    params = bytearray(open(params_file, "rb").read())

    if not ctx:
        ctx = tvm.cpu()

    # load parameters
    if not debug:
        module = tvm.contrib.graph_runtime.create(graph, lib, ctx)  # Deploye Module
    else:
        module = tvm.contrib.debugger.debug_runtime.create(graph,lib,ctx)
    module.load_params(params)
    # module.set_input(**params)
    return module



def evaluate(mod,input_shape,ctx):

    data_tvm = tvm.nd.array((np.random.uniform(size=input_shape)).astype('float32'))
    mod.set_input('data', data_tvm)
    # mod.set_input(**params)
    # evaluate
    logging.info("Evaluate inference time cost...")
    ftimer = mod.module.time_evaluator("run", ctx, number=1, repeat=60)
    prof_res = np.array(ftimer().results) * 1000  # convert to millisecond
    logging.info("Mean inference time (std dev): %.2f ms (%.2f ms)" % (np.mean(prof_res), np.std(prof_res)))



if __name__ == '__main__':
    
    mod,params,input_shape = get_mxnet_model('resnet18_v1', 1)

    logging.info(mod['main'].astext(show_meta_data=False))

    ctx = tvm.cpu()
    target = 'llvm -mcpu=core-avx2'

    # Configure the quantization behavior
    qconfig = tvm.relay.quantize.qconfig(skip_conv_layers=[0],
                    nbit_input=8,
                    nbit_weight=8,
                    global_scale=8.0,
                    dtype_input='int8',
                    dtype_weight='int8',
                    dtype_activation='int8',
                    debug_enabled_ops=None)

    mod = quantize_relay_module(mod,params,qconfig)

    # autotvm_tune(mod['main'], params, target)

    # graph,lib,params = build_module(mod, params, target,'tuning_resnet18v1.log')

    # save_compiled_module(graph, lib, params, "model")

    # mod = load_module("model",ctx,True)
    # evaluate(mod,input_shape,ctx)