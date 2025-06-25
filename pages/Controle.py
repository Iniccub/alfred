import streamlit as st
from datetime import datetime
from departamentos import departamentos
import sys
import os
import pandas as pd
import plotly.express as px

# Adiciona o diretório pai ao path para importar funções do Alfredo.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Alfredo import carregar_eventos

st.title("Controle de Reuniões por Departamento")

# Função para calcular o percentual de agendamentos por mês
def calcular_percentual_mensal():
    # Carregar eventos se não estiverem na sessão
    if 'events' not in st.session_state:
        st.session_state.events = carregar_eventos()
    
    # Inicializar dicionário para contar reuniões por mês
    meses_dict = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Inicializar contadores
    total_departamentos = len(departamentos)
    reunioes_por_mes = {mes: 0 for mes in range(1, 13)}
    
    # Ano atual
    ano_atual = datetime.now().year
    
    # Contar reuniões por mês para cada departamento
    for dept in departamentos:
        for mes in range(1, 13):
            if tem_reuniao_agendada_por_mes(dept, mes, ano_atual):
                reunioes_por_mes[mes] += 1
    
    # Calcular percentuais
    percentuais = {}
    for mes, count in reunioes_por_mes.items():
        percentuais[mes] = (count / total_departamentos) * 100 if total_departamentos > 0 else 0
    
    # Criar DataFrame para o gráfico
    df = pd.DataFrame({
        'Mês': [meses_dict[mes] for mes in range(1, 13)],
        'Percentual': [percentuais[mes] for mes in range(1, 13)]
    })
    
    return df

# Função para verificar se há reunião agendada para o departamento em um mês específico do ano especificado
def tem_reuniao_agendada_por_mes(departamento, mes, ano):
    if 'events' not in st.session_state:
        return False
        
    for evento in st.session_state.events:
        # Tratamento para diferentes formatos de data
        try:
            # Tenta converter a data do evento para objeto datetime
            if 'Z' in evento['start']:
                data_evento = datetime.fromisoformat(evento['start'].replace('Z', '+00:00'))
            else:
                data_evento = datetime.fromisoformat(evento['start'])
                
            # Verifica se o evento é do departamento, mês e ano corretos
            if (data_evento.month == mes and 
                data_evento.year == ano and
                f"Departamento: {departamento}" in evento['description']):
                return True
        except (ValueError, KeyError) as e:
            continue
    return False

# Criar e exibir o gráfico de evolução mensal
df_percentuais = calcular_percentual_mensal()
fig = px.line(
    df_percentuais, 
    x='Mês', 
    y='Percentual',
    title=f'Evolução do Percentual de Agendamentos por Mês ({datetime.now().year})',
    markers=True
)

# Adicionar rótulos de dados e ocultar a coluna de percentual
fig.update_traces(
    texttemplate='%{y:.1f}%',  # Formato do rótulo com 1 casa decimal e símbolo de percentual
    textposition='top center'   # Posição do rótulo acima do ponto
)

fig.update_layout(
    xaxis_title='Mês',
    yaxis_title='Percentual de Departamentos (%)',
    yaxis=dict(range=[0, 100],
    showticklabels=True),
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# Filtro de mês
meses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Usa o mesmo estado de sessão que a página principal
if 'mes_selecionado' not in st.session_state:
    st.session_state.mes_selecionado = meses[datetime.now().month - 1]

mes_selecionado = st.selectbox(
    "Selecione o Mês",
    meses,
    index=meses.index(st.session_state.mes_selecionado),
    on_change=lambda: setattr(st.session_state, 'mes_selecionado', meses[meses.index(st.session_state.mes_selecionado)])
)

# Converte nome do mês para número (1-12)
mes_numero = meses.index(mes_selecionado) + 1

# Inicializa eventos se não estiverem na sessão
if 'events' not in st.session_state:
    st.session_state.events = carregar_eventos()

# Função para verificar se há reunião agendada para o departamento no mês
def tem_reuniao_agendada(departamento, mes):
    if 'events' not in st.session_state:
        return False
        
    for evento in st.session_state.events:
        # Tratamento para diferentes formatos de data
        try:
            # Tenta converter a data do evento para objeto datetime
            if 'Z' in evento['start']:
                data_evento = datetime.fromisoformat(evento['start'].replace('Z', '+00:00'))
            else:
                data_evento = datetime.fromisoformat(evento['start'])
                
            # Verifica se o evento é do departamento e mês corretos
            if (data_evento.month == mes and 
                f"Departamento: {departamento}" in evento['description']):
                return True
        except (ValueError, KeyError) as e:
            st.error(f"Erro ao processar evento: {e}")
            continue
    return False

# Calcula o percentual de reuniões agendadas
total_departamentos = len(departamentos)
departamentos_com_reuniao = sum(1 for dept in departamentos if tem_reuniao_agendada(dept, mes_numero))
percentual = (departamentos_com_reuniao / total_departamentos) * 100 if total_departamentos > 0 else 0

# Exibe o indicador de progresso
st.header(f"Status das Reuniões - {mes_selecionado}")
col_prog1, col_prog2 = st.columns([1, 3])
with col_prog1:
    st.metric("Progresso", f"{percentual:.1f}%")
with col_prog2:
    st.progress(percentual / 100)

# Estatísticas adicionais
col_stats1, col_stats2, col_stats3 = st.columns(3)
with col_stats1:
    st.metric("Total de Departamentos", total_departamentos)
with col_stats2:
    st.metric("Reuniões Agendadas", departamentos_com_reuniao)
with col_stats3:
    st.metric("Pendentes", total_departamentos - departamentos_com_reuniao)

st.divider()

# Cria colunas para a tabela
col1, col2, col3 = st.columns([2, 1, 2])

# Cabeçalho da tabela
with col1:
    st.subheader("Departamento")
with col2:
    st.subheader("Status")
with col3:
    st.subheader("Ações")

# Linha divisória
st.divider()

# Adicione o filtro de status antes da listagem dos departamentos
opcoes_filtro = ["Todos", "Apenas Agendadas", "Apenas Pendentes"]
filtro_status = st.selectbox("Filtrar departamentos por status", opcoes_filtro)

# Lista os departamentos e seus status
for dept in departamentos:
    tem_reuniao = tem_reuniao_agendada(dept, mes_numero)
    
    # Aplica o filtro escolhido
    if filtro_status == "Apenas Agendadas" and not tem_reuniao:
        continue
    if filtro_status == "Apenas Pendentes" and tem_reuniao:
        continue

    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.write(dept)
    
    with col2:
        if tem_reuniao:
            st.success("✓ Agendada")
        else:
            st.warning("⚠ Pendente")
    
    with col3:
        if not tem_reuniao:
            if st.button("Agendar Reunião", key=f"btn_{dept}"):
                st.session_state.departamento_selecionado = dept
                st.switch_page("Alfredo.py")


# Configuração de tema e cores
st.markdown(
    """
    <style>
        /* Cor primária para elementos principais */
        .stButton > button {
            background-color: #4D268C;
            color: white;
        }
        
        /* Cores para métricas */
        [data-testid="metric-container"] {
            background-color: #F5F3FA;
            padding: 1rem;
            border-radius: 5px;
        }
        
        [data-testid="metric-container"] label {
            color: #4D268C;
        }
        
        /* Cores para progress bar */
        .stProgress > div > div {
            background-color: #4D268C;
        }
        
        /* Cores para status */
        .success {
            color: #4D268C;
        }
        
        .warning {
            color: #FFB347;
        }
    </style>
    """,
    unsafe_allow_html=True
)