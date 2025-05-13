import streamlit as st
from datetime import datetime
from departamentos import departamentos

st.title("Controle de Reuniões por Departamento")

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

# Função para verificar se há reunião agendada para o departamento no mês
def tem_reuniao_agendada(departamento, mes):
    if 'events' not in st.session_state:
        return False
        
    for evento in st.session_state.events:
        data_evento = datetime.fromisoformat(evento['start'].replace('Z', '+00:00'))
        if (data_evento.month == mes and 
            f"Departamento: {departamento}" in evento['description']):
            return True
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

# Lista os departamentos e seus status
for dept in departamentos:
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.write(dept)
    
    with col2:
        tem_reuniao = tem_reuniao_agendada(dept, mes_numero)
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