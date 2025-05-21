# CHATBOT COM DETECÇÃO DE INTENÇÃO USANDO spaCy + RAPIDFUZZ + EMBEDDINGS + BERTIMBAU

import pymysql
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf
from rapidfuzz import process
import spacy
from os import environ

# Carregar modelo spaCy para português
nlp = spacy.load("pt_core_news_sm")

# Função para lematizar as palavras usando spaCy
def lematizar(texto):
    doc = nlp(texto.lower())
    return [token.lemma_ for token in doc if not token.is_punct and not token.is_space]


def connect_to_db(host, port, user, password, db_name):
    return pymysql.connect(host=host, port=int(port), user=user, password=password, database=db_name, ssl={"teste": True})


def inicializar_modelos():
    # Carregamento dos modelos
    modelo_embeddings = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    modelo_bertimbau = TFAutoModelForSequenceClassification.from_pretrained("neuralmind/bert-base-portuguese-cased")
    tokenizer_bertimbau = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased", truncation=True, max_length=512)

    # Lista de intenções
    lista_intencoes = [
        "tempo_conclusao", "progresso", "certificado", "suporte", "feedback", "instituicao",
        "duracao", "meus_cursos", "obrigatorios", "proximo_modulo", "conclusao",
        "senha", "alterar_email", "cancelamento", "atividades"
    ]
    intencoes_embeddings = modelo_embeddings.encode(lista_intencoes)

    # Lemas associados a intenções
    lemas_por_intencao = {
        "tempo_conclusao": ["tempo", "concluir", "restar", "prazo", "terminar", "estimar"],
        "progresso": ["progresso", "etapa", "andamento", "evoluir"],
        "certificado": ["certificado", "diploma"],
        "suporte": ["ajudar", "suporte", "atender", "socorrer"],
        "feedback": ["avaliar", "comentar", "opinar"],
        "instituicao": ["instituição", "faculdade", "universidade", "escola"],
        "duracao": ["duração", "tempo", "limitar", "período"],
        "meus_cursos": ["curso", "aula", "matricular", "inscrever"],
        "obrigatorios": ["obrigar", "necessário", "requisito", "exigir"],
        "proximo_modulo": ["módulo", "seguir", "etapa", "próximo", "passar", "lição", "depois"],
        "conclusao": ["concluir", "finalizar", "terminar", "completar", "encerrar"],
        "senha": ["senha", "acesso", "login", "esquecer"],
        "alterar_email": ["email", "mudar", "trocar", "atualizar", "corrigir", "editar"],
        "cancelamento": ["cancelar", "remover", "excluir", "desativar"],
        "atividades": ["atividade", "tarefa", "pendência", "exercício", "entregar"]
    }

    return {
        'modelo_embeddings': modelo_embeddings,
        'modelo_bertimbau': modelo_bertimbau,
        'tokenizer_bertimbau': tokenizer_bertimbau,
        'lista_intencoes': lista_intencoes,
        'intencoes_embeddings': intencoes_embeddings,
        'lemas_por_intencao': lemas_por_intencao
    }

# Consulta ao banco

def consultar_bd(query, params=None):
    conn = connect_to_db(environ['DB_HOST'], environ['DB_PORT'], environ['DB_USER'], environ['DB_PASSWORD'], environ['DB_NAME'])
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()

# Detecção por lematização com spaCy
def detectar_por_lematizacao(texto, lista_intencoes, lemas_por_intencao):
    lemas = lematizar(texto)
    scores = {intencao: 0 for intencao in lista_intencoes}
    for intencao, lemas_alvo in lemas_por_intencao.items():
        for lema in lemas:
            if lema in lemas_alvo:
                scores[intencao] += 1
    melhor = max(scores, key=scores.get)
    return melhor if scores[melhor] > 0 else None

# Correção por similaridade usando rapidfuzz

def corrigir_palavras(texto, lista_intencoes):
    palavras = texto.lower().split()
    for palavra in palavras:
        resultado = process.extractOne(palavra, lista_intencoes, score_cutoff=80)
        if resultado:
            return resultado[0]
    return None

# Camadas embeddings e BERT
def buscar_intencao_com_embeddings(pergunta, modelo_embeddings, lista_intencoes, intencoes_embeddings):
    pergunta_embed = modelo_embeddings.encode([pergunta])
    similaridade = cosine_similarity(pergunta_embed, intencoes_embeddings)
    if similaridade[0].max() < 0.7:
        return None
    return lista_intencoes[similaridade[0].argmax()]

def buscar_intencao_com_bertimbau(pergunta, modelo_bertimbau, tokenizer_bertimbau, lista_intencoes):
    inputs = tokenizer_bertimbau(pergunta, return_tensors="tf", truncation=True, padding=True, max_length=512)
    outputs = modelo_bertimbau(**inputs)
    pred = tf.argmax(outputs.logits, axis=-1).numpy()[0]
    prob = tf.nn.softmax(outputs.logits, axis=-1).numpy()[0][pred]
    return lista_intencoes[pred] if prob > 0.7 else None

# Consulta por intenção

def buscar_dados_no_bd(usuario_id, intencao):
    if intencao == "tempo_conclusao":
        return "Seu tempo de conclusão varia de acordo com seu progresso no curso."
    if intencao == "progresso":
        query = '''
        SELECT c.name, COUNT(up.stepId)
        FROM UserProgress up 
        JOIN Enrollments e ON up.enrollmentId = e.id
        JOIN Users u ON e.userId = u.id
        JOIN Courses c ON e.courseId = c.id
        WHERE u.email = %s GROUP BY c.name'''
        r = consultar_bd(query, (usuario_id,))
        return '\n'.join(f"{x[0]}: {x[1]} etapas" for x in r) if r else "Você ainda não começou nenhum curso."
    if intencao == "certificado":
        query = '''
        SELECT c.name 
        FROM Courses c 
        JOIN Enrollments e ON c.id = e.courseId 
        JOIN Users u ON e.userId = u.id
        WHERE u.email = %s AND e.isActive = 1'''
        r = consultar_bd(query, (usuario_id,))
        return "Cursos com certificado: " + ', '.join(x[0] for x in r) if r else "Nenhum certificado disponível."
    respostas_fixas = {
        "suporte": "Entre em contato com suporte pelo email docentify@gmail.com",
        "feedback": "Você pode avaliar os cursos na seção 'Avaliações'.",
        "instituicao": "Consulte sua instituição no seu painel de cursos.",
        "duracao": "Os cursos têm durações variadas, conforme o conteúdo.",
        "meus_cursos": "Seus cursos estão listados no painel de controle.",
        "obrigatorios": "Consulte a instituição para saber os cursos obrigatórios.",
        "proximo_modulo": "O próximo módulo pode ser acessado no painel do curso.",
        "conclusao": "Você pode verificar sua conclusão no seu painel de aluno.",
        "senha": "Caso tenha esquecido sua senha, redefina-a na página de login.",
        "alterar_email": "Para alterar seu email, acesse suas configurações de perfil.",
        "cancelamento": "Para cancelar sua matrícula, entre em contato com a instituição.",
        "atividades": "Acesse seu painel para ver atividades pendentes e concluídas."
    }
    return respostas_fixas.get(intencao, "Não encontrei informações relevantes para sua pergunta.")

# Predição da intenção

def prever_intencao(pergunta, usuario_id, contexto={'tentativas': 0}):
    modelos = inicializar_modelos()
    intencao = detectar_por_lematizacao(pergunta, modelos['lista_intencoes'], modelos['lemas_por_intencao'])
    if not intencao:
        intencao = corrigir_palavras(pergunta, modelos['lista_intencoes'])
    if not intencao:
        intencao = buscar_intencao_com_embeddings(pergunta, modelos['modelo_embeddings'], modelos['lista_intencoes'], modelos['intencoes_embeddings'])
    if not intencao:
        intencao = buscar_intencao_com_bertimbau(pergunta, modelos['modelo_bertimbau'], modelos['tokenizer_bertimbau'], modelos['lista_intencoes'])
    if intencao:
        return {
            'message': buscar_dados_no_bd(usuario_id, intencao),
            'context': contexto
        }
    if contexto['tentativas'] < 2:
        contexto['tentativas'] += 1
        return {
            'message': 'Não entendi sua pergunta. Pode repetir, por favor?',
            'context': contexto
        }
    else:
        return {
            'message': 'Infelizmente não consegui entender sua solicitação.\nMas fique tranquilo que o nosso suporte poderá lhe ajudar através do email\n---> docentify@gmail.com <---',
            'context': {
                'tentativas': 0
            }
        }
