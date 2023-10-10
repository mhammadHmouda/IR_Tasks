import org.json4s.DefaultFormats
import org.json4s.jackson.Serialization

object Utils {

  def convertToJson(wordDocInfos: Iterator[WordDocumentInfo]): Iterator[String] = {
    implicit val formats: DefaultFormats.type = DefaultFormats
    wordDocInfos.map(wordDocInfo => Serialization.write(wordDocInfo))
  }

  def getIntersection(prevWordPositions: Map[Int, List[Int]], docPositions: Map[Int, List[Int]]): List[Int] = {
    val s = prevWordPositions.filter(item => docPositions.contains(item._1)
      && item._2.exists(num1 => docPositions.getOrElse(item._1, List.empty).contains(num1 + 1)))

    s.keys.toList
  }

  def getStopWords: Set[String] = {
    val stopWords = Set("the", "and", "is", "in", "for", "of", "with", "on", "at")
    stopWords
  }
}
