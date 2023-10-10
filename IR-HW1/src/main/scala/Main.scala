import org.apache.log4j.BasicConfigurator
import org.apache.log4j.varia.NullAppender
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.execution.streaming.CommitMetadata.format
import org.json4s.jackson.JsonMethods._


object Main {

  def main(args: Array[String]): Unit = {
    BasicConfigurator.configure(new NullAppender())

    val session = SparkSession.builder()
      .appName("Positional Inverted Index")
      .master("local[*]")
      .getOrCreate()

    val sc = session.sparkContext


    // Inverted Index Creation
    val invertedIndex = IndexOperations.create()(sc)

    invertedIndex.take(10).foreach(println)
    println()

    invertedIndex.coalesce(1).saveAsTextFile("src/main/resources/outputs/invertedIndex")


    // Phrase query
    val invertedIndexInfo = invertedIndex
      .map(line => parse(line).extract[WordDocumentInfo])

    val queryPhrase = "spreading extensive propaganda"
    val documentsIds = IndexOperations.query(queryPhrase, invertedIndexInfo)

    println("The phrase: (" + queryPhrase + ") exist in (" + documentsIds.size + "): " + documentsIds.mkString(", "))
    println()




    // Update Inverted Index
    val newDocument = sc.textFile("src/main/resources/1001.html")

    val newUpdated = IndexOperations.insert(newDocument, 1001, invertedIndexInfo)

    newUpdated.take(10).foreach(println)
    println()

    newUpdated.coalesce(1)
      .saveAsTextFile("src/main/resources/outputs/invertedIndexAfterInsertDoc")




    // Delete Document From Inverted Index
    val invertedIndexAfterDeleteDoc = IndexOperations.delete(4, invertedIndexInfo)

    invertedIndexAfterDeleteDoc.take(10).foreach(println)

    invertedIndexAfterDeleteDoc.coalesce(1)
      .saveAsTextFile("src/main/resources/outputs/invertedIndexAfterDeleteDoc")



    sc.stop()
  }
}
