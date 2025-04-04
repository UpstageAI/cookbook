from .selector import selector
from .generator import generator
from .getcontent import get_content
from dotenv import load_dotenv
load_dotenv()
def getPrecedent(prompt, n=3):
    files = selector(prompt, n = 3)
    out = []
    for file in files:
        out.append(generator(get_content('./referecnes/ocr_outputs/'+file)))
    return "\n\n".join([i['no']+'\n'+i['situation']+'\n'+i['judgement']+'\n'+i['evidence'] for i in out])
     
