import Utils.{convertToJson, getStopWords}
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD

object IndexOperations {

  def create()(sc: SparkContext): RDD[String] = {
    val filesRDD = sc.wholeTextFiles("src/main/resources/docs")

    filesRDD.zipWithIndex.map(item => item._1._1.stripPrefix("file:/") + "," + (item._2 + 1))
      .coalesce(1).saveAsTextFile("src/main/resources/outputs/mapping")

    val wordPositions = filesRDD.zipWithIndex.map(t => (t._2.toInt + 1, t._1._2))
      .flatMap(x => Utils.cleanSentence(x._2).split("\\s+").zipWithIndex
          .filter(wordPerIndex => wordPerIndex._1.length >= 3 && !getStopWords.contains(wordPerIndex._1.toLowerCase))
          .map(wordPerIndex => ((x._1, wordPerIndex._1.toLowerCase), List(wordPerIndex._2 + 1)))
      ).reduceByKey((list1, list2) => list1 ++ list2).sortBy(t => t._1._1)

//    wordPositions.persist(StorageLevel.MEMORY_AND_DISK)

    val positionInvertedIndex = wordPositions
      .map(item => (item._1._2, List((item._1._1, item._2))))
      .reduceByKey((x, y) => x ++ y)
      .mapValues(list => (list.size, list.toMap))
      .map(item => WordDocumentInfo(item._1, item._2._1, item._2._2))
      .sortBy(item => item.word)
      .mapPartitions(convertToJson)

    positionInvertedIndex
  }

  def insert(newDocument: RDD[String], docId: Int, existingInvertedIndex: RDD[WordDocumentInfo]): RDD[String] = {
    val newExist = existingInvertedIndex.map(line => (line.word, (line.docCount, line.docPositions)))

    val wordPositions = newDocument
      .flatMap(line =>
        Utils.cleanSentence(line).split("\\s+").zipWithIndex
          .filter(t => t._1.length >= 3 && !getStopWords.contains(t._1.toLowerCase))
          .groupBy(t => t._1.toLowerCase())
          .map(t => (t._1, (1, Map(docId -> t._2.map(pos => pos._2 + 1).toList))))
      )

    val updatedInvertedIndex = newExist.union(wordPositions)
      .reduceByKey((x, y) => (x._1, y._2 ++ x._2))

    updatedInvertedIndex
      .map(line => WordDocumentInfo(line._1, line._2._1 + 1, line._2._2))
      .mapPartitions(convertToJson)
  }

  def delete(docId: Int, existingInvertedIndex: RDD[WordDocumentInfo]): RDD[String] = {
    val updatedIndex = existingInvertedIndex.map(item => {
      val res = item.docPositions.filter(t => t._1 != docId)
      WordDocumentInfo(item.word, res.size, res)
    }).filter(item => item.docCount != 0).mapPartitions(convertToJson)
    updatedIndex
  }

  def query(queryPhrase: String, info: RDD[WordDocumentInfo]): List[Int] = {
    val queryWords = queryPhrase.split(" ")

    var prevWordPositions: Map[Int, List[Int]] = Map()
    var ids: List[Int] = List()

    queryWords.foreach(word => {
      val newInfo = info.filter(_.word.equalsIgnoreCase(word))

      if (newInfo.isEmpty())
        return List(-1)

      if (prevWordPositions.isEmpty) {
        prevWordPositions = newInfo.first().docPositions
        ids = prevWordPositions.keys.toList
      }
      else {
        ids = ids.intersect(Utils.getIntersection(prevWordPositions, newInfo.first().docPositions))
        prevWordPositions = newInfo.first().docPositions
      }
    })

    ids
  }
}
