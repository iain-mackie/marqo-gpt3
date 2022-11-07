
import marqo
import json
import openai
from urllib.parse import urlparse

TARGET_QID = 'history-12'
TOPICS_PATH = './data/CODEC/topics/topics.json'
DOC_QRELS_PATH = './data/CODEC/qrels/document_binary.qrels'
DOC_CORPUS_PATH = './data/document_corpus/codec_documents.jsonl'
DOC_INDEX_NAME = f'codec-{TARGET_QID}-doc-index'

# init GPT3 API
openai.organization = None
openai.api_key = None

if __name__ == '__main__':

    print('Establishing connection to marqo client.')
    mq = marqo.Client(url='http://localhost:8882')

    print('loading CODEC topics')
    with open(TOPICS_PATH, 'r') as f_top:
        topics = json.load(f_top)

    #########################################################################
    ######################### MARQO INDEXING ################################
    #########################################################################

    def get_target_docids(qrels_path):
        """ Get dict of docids that are relevant for TARGET_QID. """
        target_docids = {}
        with open(qrels_path, 'r') as f_doc_qrels:
            for line in f_doc_qrels:
                qid, _, docid, R = line.strip().split()
                if (qid == TARGET_QID) and (int(R) == 1):
                    target_docids[docid] = None
        return target_docids

    try:
        print(f'document index build: {mq.index(DOC_INDEX_NAME).get_stats()}')
    except KeyboardInterrupt:
        raise
    except:
        print('*** Building document index ***')
        target_docids = get_target_docids(qrels_path=DOC_QRELS_PATH)
        marqo_documents = []
        batch = 0
        with open(DOC_CORPUS_PATH, 'r') as f_doc_corpus:
            for line in f_doc_corpus:
                doc = json.loads(line)
                if doc['id'] in target_docids:
                    # Build marqo document
                    new_doc = {
                        '_id': doc['id'],
                        'Title': doc['title'],
                        'Description': doc['contents'],
                    }
                    marqo_documents.append(new_doc)

        print('Indexing documents')
        mq.index(DOC_INDEX_NAME).add_documents(marqo_documents)
        print('Done')

    # mq.index(DOC_INDEX_NAME).delete()

    #########################################################################
    ######################### GPT3 GENERATION ###############################
    #########################################################################

    def get_no_context_prompt(query):
        """ GPT3 prompt without any context. """
        return f'QUESTION: {query}\n\nANSWER:'

    def get_context_prompt(query, context):
        """ GPT3 prompt without text-based context from marqo search. """
        return f'QUESTION: {query}\n\nCONTEXT: {context}\n\nANSWER:'

    def prompt_to_essay(prompt):
        """ Process GPT-3 prompt and clean string . """
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=0.7,
            max_tokens=256,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response['choices'][0]['text'].strip().replace('\n', ' ')


    query = topics[TARGET_QID]['Query']
    narrative = topics[TARGET_QID]['Guidelines']
    print(f'qid: {TARGET_QID}')
    print(f'QUERY: {query}')
    print(f'DOMAIN EXPERT ANSWER: {narrative}')

    print('')
    print('========================================================')
    print('====================== NO CONTEXT ======================')
    prompt = get_no_context_prompt(query=query)
    print(f'Prompt: {prompt}')

    essay = prompt_to_essay(prompt)
    print(essay)

    print('')
    print('=========================================================')
    print('========= WITH MARQO DOCUMENT CONTEXT ===================')
    results = mq.index(DOC_INDEX_NAME).search(q=query, limit=5)
    context = ''
    for hit in results['hits']:
        for section, text in hit['_highlights'].items():
            context += text + '\n'
    prompt = get_context_prompt(query=query, context=context)
    print(f'Prompt: {prompt}')

    essay = prompt_to_essay(prompt)
    print(essay)
