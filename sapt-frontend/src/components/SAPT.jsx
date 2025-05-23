// SAPT.jsx - Versão completa
import React, { useState, useEffect } from "react";

// LISTA OS 62 MUNICÍPIOS do Amazonas
const municipiosAmazonas = [
  "Alvarães", "Amaturá", "Anamã", "Anori", "Apuí", "Atalaia do Norte", "Autazes", "Barcelos",
  "Barreirinha", "Benjamin Constant", "Beruri", "Boa Vista do Ramos", "Boca do Acre", "Borba", "Caapiranga", 
  "Canutama", "Carauari", "Careiro", "Careiro da Várzea", "Coari", "Codajás", "Eirunepé", "Envira", 
  "Fonte Boa", "Guajará", "Humaitá", "Ipixuna", "Iranduba", "Itacoatiara", "Itamarati", "Itapiranga", 
  "Japurá", "Juruá", "Jutaí", "Lábrea", "Manacapuru", "Manaquiri", "Manaus", "Manicoré", "Maraã", 
  "Maués", "Nhamundá", "Nova Olinda do Norte", "Novo Airão", "Novo Aripuanã", "Parintins", "Pauini", 
  "Presidente Figueiredo", "Rio Preto da Eva", "Santa Isabel do Rio Negro", "Santo Antônio do Içá", 
  "São Gabriel da Cachoeira", "São Paulo de Olivença", "São Sebastião do Uatumã", "Silves", "Tabatinga", 
  "Tapauá", "Tefé", "Tonantins", "Uarini", "Urucará", "Urucurituba"
];

// Constrói automaticamente prefeituras e câmaras
const prefeiturasAmazonas = municipiosAmazonas.map(nome => `Prefeitura de ${nome}`);
const camarasAmazonas = municipiosAmazonas.map(nome => `Câmara Municipal de ${nome}`);

// Mapeamento de dimensões para os critérios
const dimensoesCriterios = {
  "1.1": "Informações Prioritárias",
  "1.2": "Informações Prioritárias",
  "1.3": "Informações Prioritárias",
  "1.4": "Informações Prioritárias",
  "2.1": "Informações Institucionais",
  "2.2": "Informações Institucionais",
  "2.3": "Informações Institucionais",
  "2.4": "Informações Institucionais",
  "2.5": "Informações Institucionais",
  "2.6": "Informações Institucionais",
  "2.7": "Informações Institucionais",
  "2.8": "Informações Institucionais",
  "2.9": "Informações Institucionais",
  "3.1": "Receitas",
  "3.2": "Receitas",
  "4.1": "Despesas",
  "4.2": "Despesas",
  "5.1": "Convênios e Transferências",
  "5.2": "Convênios e Transferências",
  "5.3": "Convênios e Transferências",
  "6.1": "Recursos Humanos",
  "6.2": "Recursos Humanos",
  "6.3": "Recursos Humanos",
  "6.4": "Recursos Humanos",
  "6.5": "Recursos Humanos",
  "6.6": "Recursos Humanos",
  "7.1": "Diárias",
  "7.2": "Diárias",
  "8.1": "Licitações",
  "8.2": "Licitações",
  "8.3": "Licitações",
  "8.4": "Licitações",
  "8.5": "Licitações",
  "8.7": "Licitações",
  "9.1": "Contratos",
  "9.2": "Contratos",
  "9.3": "Contratos",
  "10.2": "Obras",
  "11.3": "Planejamento e Prestação de contas",
  "11.5": "Planejamento e Prestação de contas",
  "11.7": "Planejamento e Prestação de contas",
  "12.1": "Serviço de Informação ao Cidadão - SIC",
  "12.2": "Serviço de Informação ao Cidadão - SIC",
  "12.3": "Serviço de Informação ao Cidadão - SIC",
  "12.4": "Serviço de Informação ao Cidadão - SIC",
  "12.5": "Serviço de Informação ao Cidadão - SIC",
  "12.6": "Serviço de Informação ao Cidadão - SIC",
  "12.7": "Serviço de Informação ao Cidadão - SIC",
  "12.8": "Serviço de Informação ao Cidadão - SIC",
  "12.9": "Serviço de Informação ao Cidadão - SIC",
  "13.1": "Acessibilidade",
  "13.2": "Acessibilidade",
  "13.3": "Acessibilidade",
  "13.4": "Acessibilidade",
  "13.5": "Acessibilidade",
  "14.1": "Ouvidorias",
  "14.2": "Ouvidorias",
  "14.3": "Ouvidorias",
  "15.1": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
  "15.2": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
  "15.3": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
  "15.4": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
  "15.5": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
  "15.6": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital"
};

export default function SAPT() {
  const [esfera, setEsfera] = useState('');
  const [matriz, setMatriz] = useState('');
  const [orgao, setOrgao] = useState('');
  const [opcoesMatriz, setOpcoesMatriz] = useState([]);
  const [opcoesOrgao, setOpcoesOrgao] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [view, setView] = useState('filtros');
  const [statusMessage, setStatusMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [totalPerguntas, setTotalPerguntas] = useState(0);
  const [perguntaAtual, setPerguntaAtual] = useState('');
  const [eventSource, setEventSource] = useState(null);

  // Atualiza Matrizes de acordo com a esfera
  useEffect(() => {
    setMatriz('');
    setOrgao('');
    if (esfera === 'Estadual') {
      setOpcoesMatriz([
        "Poder Executivo",
        "Poder Legislativo",
        "Poder Judiciário",
        "Tribunal de Contas",
        "Ministério Público",
        "Defensoria",
        "Consórcios Públicos",
        "Estatais"
      ]);
    } else if (esfera === 'Municipal') {
      setOpcoesMatriz(["Poder Executivo", "Poder Legislativo"]);
    } else {
      setOpcoesMatriz([]);
    }
  }, [esfera]);

  // Atualiza órgãos de acordo com a matriz e esfera
  useEffect(() => {
    setOrgao('');
    if (esfera === 'Estadual') {
      switch (matriz) {
        case "Poder Executivo":
          setOpcoesOrgao(["Governo do Estado do Amazonas"]);
          break;
        case "Poder Legislativo":
          setOpcoesOrgao(["Assembleia Legislativa do Estado do Amazonas"]);
          break;
        case "Poder Judiciário":
          setOpcoesOrgao(["Tribunal de Justiça do Amazonas"]);
          break;
        case "Tribunal de Contas":
          setOpcoesOrgao(["Tribunal de Contas do Estado do Amazonas"]);
          break;
        case "Ministério Público":
          setOpcoesOrgao(["Ministério Público do Estado do Amazonas"]);
          break;
        case "Defensoria":
          setOpcoesOrgao(["Defensoria Pública do Estado do Amazonas"]);
          break;
        case "Consórcios Públicos":
          setOpcoesOrgao(["Consórcio Interestadual de Desenvolvimento Sustentável da Amazônia Legal"]);
          break;
        case "Estatais":
          setOpcoesOrgao([
            "Companhia de Saneamento do Amazonas - COSAMA",
            "Processamento de Dados Amazonas S/A - PRODAM",
            "Companhia de Gás do Amazonas - CIGÁS"
          ]);
          break;
        default:
          setOpcoesOrgao([]);
      }
    } else if (esfera === 'Municipal') {
      if (matriz === "Poder Executivo") {
        setOpcoesOrgao(prefeiturasAmazonas);
      } else if (matriz === "Poder Legislativo") {
        setOpcoesOrgao(camarasAmazonas);
      } else {
        setOpcoesOrgao([]);
      }
    } else {
      setOpcoesOrgao([]);
    }
  }, [esfera, matriz]);

  // Limpar EventSource quando o componente é desmontado
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  // Função para parar a consulta
  const pararConsulta = async () => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    
    // Enviar solicitação para o backend cancelar o processamento
    try {
      const response = await fetch('http://localhost:5000/api/cancelar-avaliacao', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setIsLoading(false);
        setStatusMessage('Avaliação interrompida pelo usuário.');
      }
    } catch (error) {
      console.error('Erro ao cancelar avaliação:', error);
      setIsLoading(false);
      setStatusMessage('Avaliação interrompida, mas pode haver processamento residual no servidor.');
    }
  };

  // Busca os resultados no backend
  // Busca os resultados no backend
async function handleBuscar() {
  if (!esfera || !matriz || !orgao) return;
  
  setIsLoading(true);
  setResultados([]);
  setStatusMessage('Iniciando avaliação...');
  setProgress(0);
  setView('resultados');

  try {
    // Primeira requisição POST para iniciar a varredura
    const initResponse = await fetch('http://localhost:5000/api/avaliar-transparencia', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ esfera, matriz, orgao })
    });
    
    if (!initResponse.ok) {
      throw new Error('Falha ao iniciar avaliação');
    }
    
    const initData = await initResponse.json();
    setTotalPerguntas(initData.totalPerguntas || 60); // Fallback para 60 se não receber o total
    setStatusMessage('Buscando site oficial e portal de transparência...');
    
    // Depois inicia o EventSource para receber os resultados
    const newEventSource = new EventSource('http://localhost:5000/api/stream-resultados');
    setEventSource(newEventSource);
    
    newEventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Se for uma mensagem de status
      if (data.type === 'status') {
        setStatusMessage(data.message);
        if (data.progress) {
          setProgress(data.progress);
        }
        if (data.perguntaAtual) {
          setPerguntaAtual(data.perguntaAtual);
        }
      } 
      // Se for um resultado de pergunta
      else {
        // Adicionar a dimensão ao resultado
        const resultadoComDimensao = {
          ...data,
          dimensao: data.dimensao || dimensoesCriterios[data.id] || "Outros"
        };
        
        setResultados(prev => [...prev, resultadoComDimensao]);
        setProgress(prev => Math.min(prev + (100 / totalPerguntas), 99));
      }
    };
    
    newEventSource.onerror = (error) => {
      console.error('Erro na conexão SSE:', error);
      newEventSource.close();
      setEventSource(null);
      setIsLoading(false);
      setStatusMessage('Erro na conexão. Tente novamente.');
    };
    
    // Quando o EventSource for fechado pelo servidor (todos os resultados foram enviados)
    newEventSource.addEventListener('complete', (event) => {
      newEventSource.close();
      setEventSource(null);
      setIsLoading(false);
      setProgress(100);
      setStatusMessage('Avaliação concluída!');
    });
    
    // Tratar erros específicos
    newEventSource.addEventListener('error', (event) => {
      const data = JSON.parse(event.data || '{}');
      newEventSource.close();
      setEventSource(null);
      setIsLoading(false);
      setStatusMessage(`Erro: ${data.message || 'Ocorreu um erro durante a avaliação'}`);
    });
    
  } catch (error) {
    console.error('Erro:', error);
    setIsLoading(false);
    setStatusMessage('Erro ao iniciar avaliação. Tente novamente.');
  }
}

  // --- VISUALIZAÇÃO ---
  if (view === 'filtros') {
    return (
      <div className="min-h-screen p-4 flex flex-col items-center bg-gray-100">
        <div className="bg-white rounded-lg shadow-lg px-6 py-8 max-w-xl w-full">
          <h1 className="text-2xl md:text-3xl font-bold text-blue-800 text-center mb-8">
            Sistema de Avaliação de Portais de Transparência
          </h1>
          {/* Filtro Esfera */}
          <div className="mb-5">
            <label className="block mb-1 font-medium">
              Selecione a Esfera:
            </label>
            <select
              className="w-full border rounded px-2 py-2"
              value={esfera}
              onChange={e => setEsfera(e.target.value)}
            >
              <option value="">Selecione...</option>
              <option value="Estadual">Estadual</option>
              <option value="Municipal">Municipal</option>
            </select>
          </div>
          {/* Filtro Matriz */}
          <div className="mb-5">
            <label className="block mb-1 font-medium">
              Matriz Específica:
            </label>
            <select
              className="w-full border rounded px-2 py-2"
              value={matriz}
              onChange={e => setMatriz(e.target.value)}
              disabled={!esfera}
            >
              <option value="">Selecione...</option>
              {opcoesMatriz.map(opc => <option key={opc} value={opc}>{opc}</option>)}
            </select>
          </div>
          {/* Filtro Órgão */}
          <div className="mb-8">
            <label className="block mb-1 font-medium">
              Órgão:
            </label>
            <select
              className="w-full border rounded px-2 py-2"
              value={orgao}
              onChange={e => setOrgao(e.target.value)}
              disabled={!matriz}
            >
              <option value="">Selecione...</option>
              {opcoesOrgao.length > 10 ? (
                <optgroup label="Órgãos">
                  {opcoesOrgao.map(opc => <option key={opc} value={opc}>{opc}</option>)}
                </optgroup>
              ) : (
                opcoesOrgao.map(opc => <option key={opc} value={opc}>{opc}</option>)
              )}
            </select>
          </div>
          {/* Botão Buscar */}
          <button
            className={`w-full py-3 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 transition disabled:bg-blue-300`}
            disabled={isLoading || !esfera || !matriz || !orgao}
            onClick={handleBuscar}
          >
            {isLoading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
      </div>
    );
  }

  // Visualização dos resultados
  if (view === 'resultados') {
    // Calcular estatísticas
    const totalItens = resultados.length;
    const atendidos = resultados.filter(item => item.disponibilidade === true).length;
    const percentualAtendimento = totalItens > 0 ? Math.round((atendidos / totalItens) * 100) : 0;
    
    // Agrupar por classificação
    const totalEssenciais = resultados.filter(item => item.classificacao === 'Essencial').length;
    const atendidosEssenciais = resultados.filter(item => item.classificacao === 'Essencial' && item.disponibilidade === true).length;
    
    const totalObrigatorias = resultados.filter(item => item.classificacao === 'Obrigatória').length;
    const atendidosObrigatorias = resultados.filter(item => item.classificacao === 'Obrigatória' && item.disponibilidade === true).length;
    
    const totalRecomendadas = resultados.filter(item => item.classificacao === 'Recomendada').length;
    const atendidosRecomendadas = resultados.filter(item => item.classificacao === 'Recomendada' && item.disponibilidade === true).length;

    return (
      <div className="min-h-screen bg-gray-100 py-8 px-4 flex flex-col items-center">
        <div className="bg-white rounded-lg shadow-lg p-6 max-w-7xl w-full">
          <button
            onClick={() => setView('filtros')}
            className="mb-4 text-blue-700 hover:underline flex items-center"
          >
            <span className="mr-1">←</span> Voltar
          </button>
          
          <h2 className="text-2xl font-bold text-blue-800 mb-3">Resultado da Avaliação</h2>
          
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="mb-2">
              <span className="font-semibold">Esfera:</span> {esfera} <br />
              <span className="font-semibold">Matriz:</span> {matriz} <br />
              <span className="font-semibold">Órgão:</span> {orgao}
            </p>
            
            {/* Barra de Progresso e Status */}
            {isLoading && (
              <div className="mt-4">
                <div className="mb-2 flex justify-between">
                  <span className="text-sm font-medium text-blue-700">{statusMessage}</span>
                  <span className="text-sm font-medium text-blue-700">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                {perguntaAtual && (
                  <div className="mt-2 text-sm text-gray-600 animate-pulse">
                    Verificando: {perguntaAtual}
                  </div>
                )}
                
                {/* Botão para parar a consulta */}
                <button
                  onClick={pararConsulta}
                  className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
                >
                  Parar Consulta
                </button>
              </div>
            )}
            
            {/* Estatísticas (só mostrar quando tiver resultados) */}
            {resultados.length > 0 && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                  <div className="text-lg font-bold text-blue-800">{percentualAtendimento}%</div>
                  <div className="text-sm text-blue-600">Atendimento Total</div>
                  <div className="text-xs text-blue-500">{atendidos} de {totalItens} itens</div>
                </div>
                
                <div className="bg-red-50 p-3 rounded-lg border border-red-200">
                  <div className="text-lg font-bold text-red-800">
                    {totalEssenciais > 0 ? Math.round((atendidosEssenciais / totalEssenciais) * 100) : 0}%
                  </div>
                  <div className="text-sm text-red-600">Essenciais</div>
                  <div className="text-xs text-red-500">{atendidosEssenciais} de {totalEssenciais} itens</div>
                </div>
                
                <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                  <div className="text-lg font-bold text-yellow-800">
                    {totalObrigatorias > 0 ? Math.round((atendidosObrigatorias / totalObrigatorias) * 100) : 0}%
                  </div>
                  <div className="text-sm text-yellow-600">Obrigatórias</div>
                  <div className="text-xs text-yellow-500">{atendidosObrigatorias} de {totalObrigatorias} itens</div>
                </div>
                
                <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                  <div className="text-lg font-bold text-green-800">
                    {totalRecomendadas > 0 ? Math.round((atendidosRecomendadas / totalRecomendadas) * 100) : 0}%
                  </div>
                  <div className="text-sm text-green-600">Recomendadas</div>
                  <div className="text-xs text-green-500">{atendidosRecomendadas} de {totalRecomendadas} itens</div>
                </div>
              </div>
            )}
          </div>
          
          {/* Cabeçalho da Matriz */}
          <div className="mb-4">
            <h3 className="text-xl font-bold text-blue-700">Matriz Comum</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full border divide-y text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="p-2 font-bold text-left">Dimensão</th>
                  <th className="p-2 font-bold text-left">ID</th>
                  <th className="p-2 font-bold text-left">Critério</th>
                  <th className="p-2 font-bold">Fundamentação</th>
                  <th className="p-2 font-bold">Classificação</th>
                  <th className="p-2 font-bold">Disponibilidade</th>
                  <th className="p-2 font-bold">Atualidade</th>
                  <th className="p-2 font-bold">Série Histórica</th>
                  <th className="p-2 font-bold">Relatórios</th>
                  <th className="p-2 font-bold">Filtro</th>
                  <th className="p-2 font-bold">Evidência</th>
                </tr>
              </thead>
              <tbody>
                {resultados.map((item, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="p-2 border-b">{item.dimensao}</td>
                    <td className="p-2 border-b">{item.id}</td>
                    <td className="p-2 border-b">{item.pergunta}</td>
                    <td className="p-2 border-b text-xs">{item.fundamentacao}</td>
                    <td className="p-2 text-center border-b">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        item.classificacao === 'Essencial' ? 'bg-red-100 text-red-800' :
                        item.classificacao === 'Obrigatória' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {item.classificacao}
                      </span>
                    </td>
                    <td className="p-2 text-center border-b">{item.disponibilidade === true ? "✅" : "❌"}</td>
                    <td className="p-2 text-center border-b">{item.atualidade === true ? "✅" : item.atualidade === false ? "❌" : "N/A"}</td>
                    <td className="p-2 text-center border-b">{item.serieHistorica === true ? "✅" : item.serieHistorica === false ? "❌" : "N/A"}</td>
                    <td className="p-2 text-center border-b">{item.gravacaoRelatorios === true ? "✅" : item.gravacaoRelatorios === false ? "❌" : "N/A"}</td>
                    <td className="p-2 text-center border-b">{item.filtroPesquisa === true ? "✅" : item.filtroPesquisa === false ? "❌" : "N/A"}</td>
                    <td className="p-2 text-center border-b">
                      {item.linkEvidencia
                        ? <a 
                            href={item.linkEvidencia} 
                            rel="noopener noreferrer" 
                            className="text-blue-600 hover:underline"
                          >
                            Link
                          </a>
                        : <span className="text-gray-400">N/A</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-6 flex justify-between">
            <button
              onClick={() => setView('filtros')}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              Nova Consulta
            </button>
            
            <button
              onClick={() => {
                // Implementação futura: exportar para PDF ou Excel
                alert('Funcionalidade de exportação em desenvolvimento');
              }}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              disabled={isLoading || resultados.length === 0}
            >
              Exportar Relatório
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Fallback
  return <div>Carregando...</div>;
}