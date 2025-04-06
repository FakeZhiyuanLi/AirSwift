import os
import multiprocessing

from faiss_db import VectorDB
import file_handler
class Main:
    @staticmethod
    def run():
        db = VectorDB()
        image_desc = file_handler.process_image_file("/Users/yashpanwar/Downloads/sunflower.jpg")
        text_desc = file_handler.process_text_file("/Users/yashpanwar/Downloads/catinthehat.txt") #/Users/yashpanwar/Downloads/dialog.txt
        #pdf_desc = file_handler.process_pdf_file("'/Users/yashpanwar/Downloads/Ch 2 Test outline.pdf'")
        csv_desc = file_handler.process_csv_file("/Users/yashpanwar/git/expressionevaluator-aden-panwayas-mvla/bin/analysis_sum.csv")
        test_documents = [
            image_desc,
            text_desc,
            csv_desc
        ]
        db.add_documents(test_documents)
        tree_context = """
        Picture with some nice scenery, looks like a flower with vibrancy.
        """
        best_doc = db.search_with_context(tree_context)
        print(f"\nBest Question for context: {best_doc['document']}")


if __name__ == '__main__':
    #Limits thread count the DB will use (for FAISS)
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    multiprocessing.set_start_method('spawn', force=True) #May avoid C-extension fork issues
    Main.run()
