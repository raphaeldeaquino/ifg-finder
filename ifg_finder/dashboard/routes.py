import requests
import json
import urllib.parse
import subprocess
import spacy
from multiprocessing import Manager
from deep_translator import MyMemoryTranslator
from flask import render_template, request, Response
from ifg_finder.dashboard import bp

api = 'https://api.lattes.bcc.ifg.edu.br/api'
manager = Manager()
progress_map = manager.dict()

subprocess.run(["python", "-m", "spacy", "download", "pt_core_news_md"])
nlp = spacy.load("pt_core_news_md")


def query_api(endpoint, keywords, request_id, i, n, types=None):
    result = {}

    for c, keyword in enumerate(keywords):
        encoded_keyword = urllib.parse.quote(keyword)
        if types:
            for type in types:
                response = requests.get(f'{api}/pesquisadores/{endpoint}?termo={encoded_keyword}&tipo={type}')
                response_dict = json.loads(response.text)
                response_list = list(response_dict.values())
                for p in response_list[0]:
                    campus = p['campus_atual'][7:] if 'CÂMPUS' in p['campus_atual'] else p['campus_atual']
                    if campus not in result:
                        result[campus] = {'Total': 0, 'Termos': {k: 0 for k in keywords}, 'Pesquisadores': []}
                    if keyword not in result[campus]['Termos']:
                        result[campus]['Termos'][keyword] = 0

                    # Verificar se o pesquisador já foi adicionado
                    already_added = any(
                        p['nome_completo'] == pesquisador['nome'] for pesquisador in result[campus]['Pesquisadores'])

                    if not already_added:
                        result[campus]['Termos'][keyword] += 1
                        result[campus]['Total'] += 1
                        result[campus]['Pesquisadores'].append({'nome': p['nome_completo'],
                                                                'email': p['email'],
                                                                'lattes': p['link_curriculo']})
        else:
            response = requests.get(f'{api}/pesquisadores/{endpoint}?termo={encoded_keyword}')
            response_dict = json.loads(response.text)
            response_list = list(response_dict.values())
            for p in response_list[0]:
                campus = p['campus_atual'][7:] if 'CÂMPUS' in p['campus_atual'] else p['campus_atual']
                if campus not in result:
                    result[campus] = {'Total': 0, 'Termos': {k: 0 for k in keywords}, 'Pesquisadores': []}
                if keyword not in result[campus]['Termos']:
                    result[campus]['Termos'][keyword] = 0

                # Verificar se o pesquisador já foi adicionado
                already_added = any(
                    p['nome_completo'] == pesquisador['nome'] for pesquisador in result[campus]['Pesquisadores'])

                if not already_added:
                    result[campus]['Termos'][keyword] += 1
                    result[campus]['Total'] += 1
                    result[campus]['Pesquisadores'].append({'nome': p['nome_completo'],
                                                            'email': p['email'],
                                                            'lattes': p['link_curriculo']})
        progress_map[request_id] = f'Fazendo consulta à API: {(c + 1) + (i * len(keywords))} de {n * len(keywords)}'

    full_result = {}
    campus = ['ÁGUAS LINDAS', 'ANÁPOLIS', 'APARECIDA DE GOIÂNIA', 'CIDADE DE GOIÁS',
              'FORMOSA', 'GOIÂNIA', 'GOIÂNIA OESTE', 'INHUMAS', 'ITUMBIARA',
              'JATAÍ', 'LUZIÂNIA', 'REITORIA', 'SENADOR CANEDO', 'URUACU',
              'VALPARAISO']
    for c in campus:
        if c in result:
            full_result[c] = {'total': result[c]['Total'], 'pesquisadores': result[c]['Pesquisadores']}
        else:
            full_result[c] = {'total': 0, 'pesquisadores': []}

    return full_result


def lemma_and_translate(keywords, request_id):
    new_keywords = set()

    for i, keyword in enumerate(keywords):
        progress_map[request_id] = f'Fazendo variações da palavra {keyword}: {i + 1} de {len(keywords)}'
        keyword_lemma = ''
        for token in nlp(keyword):
            keyword_lemma += token.lemma_ + " "
        keyword_lemma = keyword_lemma.strip()
        new_keywords.add(keyword)
        new_keywords.add(keyword_lemma)
        translated = MyMemoryTranslator(source="pt-BR", target="en-US").translate(text=keyword)
        new_keywords.add(translated)
        translated = MyMemoryTranslator(source="pt-BR", target="en-US").translate(text=keyword_lemma)
        new_keywords.add(translated)

    return list(new_keywords)


@bp.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        request_id = request.form.get('requestId')

        # Captura as palavras-chave
        keywords = request.form.getlist('keywords')
        keywords = keywords[0].split(';')
        keywords = lemma_and_translate(keywords, request_id)

        # Captura os checkboxes selecionados
        selected_fields = request.form.getlist('selected_fields')

        i = 0
        if 'formacao' in selected_fields:
            result_education = query_api('formacao', keywords, request_id, i, len(selected_fields))
            i = i + 1
        else:
            result_education = None
        if 'atuacao' in selected_fields:
            result_acting = query_api('atuacao', keywords, request_id, i, len(selected_fields))
            i = i + 1
        else:
            result_acting = None
        if 'banca' in selected_fields:
            result_jury = query_api('banca', keywords, request_id, i, len(selected_fields))
            i = i + 1
        else:
            result_jury = None
        if 'orientacao' in selected_fields:
            result_advisor = query_api('orientacao', keywords, request_id, i, len(selected_fields), [1, 2, 3, 4, 5, 6])
            i = i + 1
        else:
            result_advisor = None
        if 'registro' in selected_fields:
            result_register = query_api('registro', keywords, request_id, i, len(selected_fields), [1, 2])
            i = i + 1
        else:
            result_register = None

        # Faça algo com os dados capturados, como passá-los para a template
        return render_template('dashboard/index.html', keywords=keywords, result_education=result_education,
                               result_acting=result_acting, result_jury=result_jury, result_advisor=result_advisor,
                               result_register=result_register)

    # Renderiza o template por padrão no método GET
    return render_template('index.html')


@bp.route('/progresso', methods=['GET'])
def progresso():
    # Obtém o requestId da query string da URL
    requestId = request.args.get('requestId')
    progress = progress_map[requestId]

    def gerar_progresso():
        return json.dumps({'progress': progress})

    return Response(gerar_progresso(), mimetype='text/plain')
