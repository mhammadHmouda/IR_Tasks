import os, glob, sys
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from spellchecker import SpellChecker
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

class DocumentSearchEngine:

    # This constructor load and process file and build tfidf for this documents, 
    # And then become able to search for any query from this index
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.documents_content, self.documents_name = self._load_and_preprocess_files()

        english_stop_words = stopwords.words('english')
        self.pipeline = Pipeline([
            ('count', CountVectorizer(lowercase=True, stop_words=english_stop_words, min_df=2, max_features=10)),
            ('tfidf', TfidfTransformer())
        ])

        self.tfidf_documents = self.pipeline.fit_transform(self.documents_content)


    # This take an text and return this text normalized
    def _normalize_text(self, text):
        spell = SpellChecker()
        stemmer = PorterStemmer()
        corrected_tokens = [spell.correction(word) for word in word_tokenize(text)]
        stemmed_tokens = [stemmer.stem(word) for word in corrected_tokens]
        return ' '.join(stemmed_tokens)


    # This for read documents, process and normalized this documents content
    def _load_and_preprocess_files(self):
        files_content = []
        files_path = []
        try:
            paths = glob.glob(os.path.join(self.folder_path, "*.txt"))

            for file_path in paths:
                with open(file_path, "rt", encoding='utf-8') as file:
                    content = file.read()
                    normalized_content = self._normalize_text(content)
                    files_content.append(normalized_content)
                    files_path.append(file_path)

            return files_content, files_path

        except Exception as e:
            print(f"An error occurred when loading and processing files: {e}")
            return None, None


    # This take query to search for this in the tfidf build in the __init__ method
    def search_top_k(self, query, k=5):
        try:
            normalized_query = self._normalize_text(query)
            tfidf_query = self.pipeline.transform([normalized_query])

            cs_score = cosine_similarity(tfidf_query, self.tfidf_documents).flatten()

            top_k_indices = cs_score.argsort()[::-1][:k]
            top_k_documents = [(self.documents_name[index], cs_score[index]) for index in top_k_indices]

            return top_k_documents

        except Exception as e:
            print(f"An error occurred during the search: {e}")
            return None
        

    # This for show results cosine similarity score for specific query
    def print_result(self, result, query):
        print(f"\nScore for ({query}):")
        for file_path, score in result:
            print(f"Document: {file_path}, Score: {score:.3f}")



# To run the program example (py tfidf.py "path_to_documents" "<query>" )
def main():
    folder_path = sys.argv[1] # "d:\\docs-tfidf"
    query1 = sys.argv[2] # "frequency"
    query2 = "importance" # for test multible query to the same index created.

    engine = DocumentSearchEngine(folder_path)

    top_k_query1 = engine.search_top_k(query1, k=5)
    top_k_query2 = engine.search_top_k(query2, k=5)

    engine.print_result(top_k_query1, query1)
    engine.print_result(top_k_query2, query2)


if __name__ == "__main__":
    main()