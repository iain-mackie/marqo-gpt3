
import marqo
import json
import openai

from news import MARQO_DOCUMENTS

# init GPT3 API
openai.organization = None
openai.api_key = None

DOC_INDEX_NAME = 'news-index'
output = './logs.txt'
queries = [
    # question                                  # date filter   # website filter
    ('What is happening in business today?',    '2022-11-09',   None ),
    ('How is the US Midterm Election going?',   None,           None ),
    ('What happened in UK yesterday?',          '2022-11-08',   'www.bbc.co.uk'),
]


if __name__ == '__main__':

    print('Establishing connection to marqo client.')
    mq = marqo.Client(url='http://localhost:8882')

    #########################################################################
    ######################### MARQO INDEXING ################################
    #########################################################################
    try:
        print(f'document index build: {mq.index(DOC_INDEX_NAME).get_stats()}')
    except KeyboardInterrupt:
        raise
    except:
        print('Indexing documents')
        mq.index(DOC_INDEX_NAME).add_documents(MARQO_DOCUMENTS)
        print('Done')

    # mq.index(DOC_INDEX_NAME).delete()

    #########################################################################
    ######################### GPT3 GENERATION ###############################
    #########################################################################

    def get_no_context_prompt(question, date, website):
        """ GPT3 prompt without any context. """
        if not date:
            date = 'Unknown'
        if not website:
            website = 'Unknown'
        return f'Title: {question}\n\nDate: {date}, Website: {website}\n\nNews summary:'

    def get_context_prompt(question, date, website, context):
        """ GPT3 prompt without text-based context from marqo search. """
        if not date:
            date = 'Unknown'
        if not website:
            website = 'Unknown'
        return f'Title: {question}\n\nDate: {date}, Website: {website}\n\nBackground:{context}\n\nNews summary:'

    def prompt_to_essay(prompt):
        """ Process GPT-3 prompt and clean string . """
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=0.0,
            max_tokens=256,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response['choices'][0]['text'].strip().replace('\n', ' ')


    #########################################################################
    ########################### EXPERIMENTS ################################
    #########################################################################

    with open(output, 'w') as f_out:
        for question, date, website in queries:
            f_out.write('////////////////////////////////////////////////////////\n')
            f_out.write('////////////////////////////////////////////////////////\n')

            f_out.write(f'question: {question}, date: {date}, website: {website}\n')

            f_out.write('================= GPT3 NO CONTEXT ======================\n')
            # Build prompt without context.
            prompt = get_no_context_prompt(question, date, website)
            f_out.write(f'Prompt: {prompt}\n')
            summary = prompt_to_essay(prompt)
            f_out.write(f'{summary}\n\n')

            f_out.write('================= GPT3 + Marqo  =======================\n')
            # Query Marqo and set filters based on user query
            if isinstance(date, str) and isinstance(website, str):
                results = mq.index(DOC_INDEX_NAME).search(q=question,
                                                          searchable_attributes=['Title', 'Description'],
                                                          filter_string=f"date:{date} AND website: {website}",
                                                          limit=5)
            elif isinstance(date, str):
                results = mq.index(DOC_INDEX_NAME).search(q=question,
                                                          searchable_attributes=['Title', 'Description'],
                                                          filter_string=f"date:{date}",
                                                          limit=5)
            elif isinstance(website, str):
                results = mq.index(DOC_INDEX_NAME).search(q=question,
                                                          searchable_attributes=['Title', 'Description'],
                                                          filter_string=f"website: {website}",
                                                          limit=5)
            else:
                results = mq.index(DOC_INDEX_NAME).search(q=question,
                                                          searchable_attributes=['Title', 'Description'],
                                                          limit=5)
            # Build context using Marqo's highlighting functionality.
            context = ''
            for hit in results['hits']:
                print(hit['Description'])
                for section, text in hit['_highlights'].items():
                    context += text + '\n'
            # Build prompt with Marqo context.
            prompt = get_context_prompt(question=question,
                                        date=date,
                                        website=website,
                                        context=context)
            f_out.write(f'Prompt: {prompt}\n')
            summary = prompt_to_essay(prompt)
            f_out.write(f'{summary}\n\n')

