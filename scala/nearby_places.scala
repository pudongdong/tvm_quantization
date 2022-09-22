package com.shopee.dp

import com.shopee.dp.HotelSearchLog.LOGGER
import org.apache.log4j.{Level, Logger}
import org.apache.spark.sql.{SaveMode, SparkSession}
import org.apache.spark.sql.functions.{col, collect_list, expr, isnull, struct, to_json}

import java.util.Properties

object HotelNearbyPlace {
  private val LOGGER = Logger.getLogger("city_info_filter")

  def main(args: Array[String]){
    val dbconfig = Map(
      "staging" -> Map(
        "host" -> "host",
        "port" -> "6606",
        "user_name" -> "user",
        "user_password" -> "password"),
      "test" -> Map(
        "host" -> "host",
        "port" -> "6606",
        "user_name" -> "user",
        "user_password" -> "password"),
      "uat" -> Map(
        "host" -> "host",
        "port" -> "6606",
        "user_name" -> "user",
        "user_password" -> "pass"),
      "live" -> Map(
        "host" -> "host",
        "port" -> "6606",
        "user_name" -> "user",
        "user_password" -> "user"),
    )

    val spark = SparkSession.builder()
      .appName("hotel nearbyplace")
      .enableHiveSupport()
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    LOGGER.setLevel(Level.DEBUG)

    spark.conf.set("spark.driver.allowMultipleContexts","true")
    spark.conf.set("hive.exec.dynamic.partition", "true")
    spark.conf.set("hive.exec.dynamic.partition.mode", "nonstrict")


    val df = spark.sql(s"select country_code,city_code,country_name," +
      s"city_name,language_id,type,name,category_name,active_hotels,tag from schema.hotel_city_filter_info_frequency_monthly;")

    val df2 = df.filter("tag='attractions'").groupBy("country_code","country_name","city_name","city_code","language_id").agg(collect_list(
      to_json(struct(
      col("type"),
      col("name"),
      col("category_name"),
      col("active_hotels")
      )
    )).alias("attractions")).selectExpr("country_code","country_name","city_name","city_code","language_id","cast(attractions as string) as attractions")


    val df3 = df.filter("tag='transportation'").groupBy("country_code","country_name","city_name","city_code","language_id").agg(collect_list(
      to_json(struct(
      col("type"),
      col("name"),
      col("category_name"),
      col("active_hotels")
      )
    )).alias("transportations")).selectExpr("country_code","country_name","city_name","city_code","language_id","cast(transportations as string) as transportations")

    val df4 = df2.join(df3,df2("city_code") === df3("city_code") && df2("language_id") === df3("language_id"),"left").select(
      df2("country_code"),
      df2("country_name"),
      df2("city_code"),
      df2("city_name"),
      df2("language_id").alias("language_code"),
      df2("attractions"),
      df3("transportations"))

    val df5 = df4.filter(col("city_name").isNotNull)
      .filter(col("city_code").isNotNull)
      .filter(col("country_code").isNotNull)
      .filter(col("country_name").isNotNull)
      .where("city_name <> ''")

    // 备份到hive中
    df5.repartition(1).createTempView("tmptable")
    spark.sqlContext.sql("drop table if exists ota_city_filter_table")
    spark.sqlContext.sql("create table schema.ota_city_filter_table as select * from tmptable")

    try {
      print("Started.......")
      // JDBC connection details
      val driver = "com.mysql.jdbc.Driver"

//      val envs = List("staging","test","uat","live")
      val envs = List("test")
      val cids = List("id","vn","my","ph","th","sg","tw")

      for (env <- envs) {
        for (cid <- cids) {
          LOGGER.info("processing %s,%s",env,cid)
          val host = dbconfig.get(env).get("host")
          val port = dbconfig.get(env).get("port")
          val url = "jdbc:mysql://%s:%s/shopee_dp_hotel_%s_db".format(host, port, cid)
          val user = dbconfig.get(env).get("user_name")
          val pass = dbconfig.get(env).get("user_password")
          val table = "city_filter_info_tab"
          df5.write.format("jdbc")
            .option("driver", driver)
            .option("url", url)
            .option("dbtable", table)
            .option("user", user)
            .option("password", pass)
            .option("batchsize", 1000)
            .option("truncate", true)
            .mode(SaveMode.Overwrite)
            .save()
        }
      }
    } catch {
      case e : Throwable => println("Connectivity Failed for Table ", e)
    }
  }
}
