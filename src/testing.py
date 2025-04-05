import os
import multiprocessing

from faiss_db import VectorDB
import file_handler
class Main:
    @staticmethod
    def run():
        # db = VectorDB()
        # test_questions = [
        #     "Could you describe the work experiences you had before your conviction?",
        #     "What types of activities have you participated in that you believe demonstrate your rehabilitation?",
        #     "Can you tell me about the organizations where you worked or volunteered before and after your incarceration?",
        #     "Can you detail any rehabilitation strategies you have implemented to stay on track?",
        #     "How have these experiences impacted your perspectives?"
        # ]
        # db.add_questions(test_questions)
        # tree_context = """
        # After my release, I started attending regular counseling sessions and enrolled in an anger management program. I also began 
        # volunteering, in my community which has kept me accountable.
        # """
        # next_question = db.search_with_context(tree_context)
        # print(f"\nBest Question for context: {next_question['question']}")
        image_desc = file_handler.process_image_file("/Users/yashpanwar/Downloads/sunflower.jpg")
        


if __name__ == '__main__':
    #Limits thread count the DB will use (for FAISS)
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    multiprocessing.set_start_method('spawn', force=True) #May avoid C-extension fork issues
    Main.run()
