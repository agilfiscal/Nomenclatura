<script setup>
import { ref, onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import MarcasParam from './components/MarcasParam.vue'
import TiposParam from './components/TiposParam.vue'
import ParticularidadesParam from './components/ParticularidadesParam.vue'
import VolumesParam from './components/VolumesParam.vue'
import AbreviacoesParam from './components/AbreviacoesParam.vue'

const file = ref(null)
const produtos = ref([])
const produtosFiltrados = ref([])
const loading = ref(false)
const error = ref("")
const filtroConfiabilidade = ref("todos")
const loadingParticularidade = ref("")

// Contadores para o dashboard
const contadores = ref({
  marcas: 0,
  tipos: 0,
  particularidades: 0,
  volumes: 0,
  abreviacoes: 0
})

const route = ref('padronizar')
const setRoute = (r) => { route.value = r }

const handleFileChange = (e) => {
  file.value = e.target.files[0]
}

// Função para buscar contadores
const fetchContadores = async () => {
  try {
    const [marcasRes, tiposRes, particularidadesRes, volumesRes, abreviacoesRes] = await Promise.all([
      fetch('http://localhost:8000/marcas/'),
      fetch('http://localhost:8000/tipos/'),
      fetch('http://localhost:8000/particularidades/'),
      fetch('http://localhost:8000/volumes/'),
      fetch('http://localhost:8000/abreviacoes/')
    ])
    
    const marcas = await marcasRes.json()
    const tipos = await tiposRes.json()
    const particularidades = await particularidadesRes.json()
    const volumes = await volumesRes.json()
    const abreviacoes = await abreviacoesRes.json()
    
    contadores.value = {
      marcas: marcas.length,
      tipos: tipos.length,
      particularidades: particularidades.length,
      volumes: volumes.length,
      abreviacoes: abreviacoes.length
    }
  } catch (e) {
    console.error('Erro ao buscar contadores:', e)
  }
}

// Função removida - o backend já retorna os campos corretos

const uploadFile = async () => {
  if (!file.value) return
  loading.value = true
  error.value = ""
  produtos.value = []
  const formData = new FormData()
  formData.append('file', file.value)
  try {
    const res = await fetch('http://localhost:8000/upload/', {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    if (data.error) {
      error.value = data.error
    } else {
      // Adicionar propriedade showTooltip para cada produto
      produtos.value = data.produtos.map(p => ({
        ...p,
        showTooltip: false
      }))
      produtosFiltrados.value = produtos.value
    }
  } catch (err) {
    error.value = 'Erro ao enviar arquivo.'
  } finally {
    loading.value = false
  }
}

// Função para alternar o tooltip
const toggleTooltip = (event, index) => {
  // Fechar todos os tooltips primeiro
  produtosFiltrados.value.forEach(p => {
    if (p.showTooltip !== undefined) {
      p.showTooltip = false
    }
  })
  
  // Abrir o tooltip do produto clicado
  produtosFiltrados.value[index].showTooltip = true
  
  // Fechar o tooltip após 5 segundos
  setTimeout(() => {
    produtosFiltrados.value[index].showTooltip = false
  }, 5000)
}

// Função para filtrar produtos por confiabilidade
const filtrarPorConfiabilidade = () => {
  switch (filtroConfiabilidade.value) {
    case "alta":
      produtosFiltrados.value = produtos.value.filter(p => p.confiabilidade >= 75)
      break
    case "media":
      produtosFiltrados.value = produtos.value.filter(p => p.confiabilidade >= 50 && p.confiabilidade < 75)
      break
    case "baixa":
      produtosFiltrados.value = produtos.value.filter(p => p.confiabilidade < 50)
      break
    default:
      produtosFiltrados.value = produtos.value
  }
}

// Função para aceitar uma particularidade sugerida
const aceitarParticularidade = async (particularidade, indexProduto) => {
  loadingParticularidade.value = particularidade
  
  try {
    const formData = new FormData()
    formData.append('nome', particularidade)
    
    const response = await fetch('http://localhost:8000/particularidades/sugerir/', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (result.status === 'adicionado') {
      // Atualizar o produto localmente
      const produto = produtosFiltrados.value[indexProduto]
      produto.particularidade = particularidade
      produto.padrao = 'TMPV'
      produto.sugestoes_particularidades = produto.sugestoes_particularidades.filter(p => p !== particularidade)
      
      // Recalcular confiabilidade
      const campos_identificados = [produto.tipo, produto.marca, produto.particularidade, produto.volume].filter(c => c).length
      produto.confiabilidade = Math.round((campos_identificados / 4) * 100)
      
      // Atualizar sugestão TMPV
      const campos = [produto.tipo, produto.marca, produto.particularidade, produto.volume]
      const campos_unicos = []
      for (const c of campos) {
        if (c && !campos_unicos.includes(c)) {
          campos_unicos.push(c)
        }
      }
      produto.sugestao_tmpv = campos_unicos.join(' ').replace(/\s+/g, ' ').trim()
      
      // Atualizar contadores
      await fetchContadores()
      
      alert(`✅ Particularidade "${particularidade}" cadastrada com sucesso!`)
    } else if (result.status === 'já_existia') {
      alert(`ℹ️ A particularidade "${particularidade}" já existe no banco de dados.`)
    } else {
      alert(`❌ Erro: ${result.mensagem}`)
    }
  } catch (error) {
    console.error('Erro ao cadastrar particularidade:', error)
    alert('❌ Erro ao cadastrar particularidade. Tente novamente.')
  } finally {
    loadingParticularidade.value = ""
  }
}

// Buscar contadores quando o componente for montado
onMounted(() => {
  fetchContadores()
})
</script>

<template>
  <div style="max-width: 1000px; margin: 2rem auto; padding: 4.5rem 2rem 2rem 2rem; border: 1px solid #eee; border-radius: 8px; background: #fff; min-height: 80vh;">
    <Navbar :route="route" @navigate="setRoute" />
    <div v-if="route === 'padronizar'">
      <!-- Tela de padronização de nomes -->
      <h1>Nomenclatura TMPV</h1>
      
      <!-- Dashboard com contadores -->
      <div class="dashboard" style="margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
        <h3 style="margin-top: 0; color: #333;">Resumo do Banco de Dados</h3>
        <div class="contadores-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
          <div class="contador-item" style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 2rem; font-weight: bold; color: #42b883;">{{ contadores.marcas }}</div>
            <div style="color: #666;">Marcas</div>
          </div>
          <div class="contador-item" style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 2rem; font-weight: bold; color: #42b883;">{{ contadores.tipos }}</div>
            <div style="color: #666;">Tipos</div>
          </div>
          <div class="contador-item" style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 2rem; font-weight: bold; color: #42b883;">{{ contadores.particularidades }}</div>
            <div style="color: #666;">Particularidades</div>
          </div>
          <div class="contador-item" style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 2rem; font-weight: bold; color: #42b883;">{{ contadores.volumes }}</div>
            <div style="color: #666;">Volumes</div>
          </div>
          <div class="contador-item" style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 2rem; font-weight: bold; color: #42b883;">{{ contadores.abreviacoes }}</div>
            <div style="color: #666;">Abreviações</div>
          </div>
        </div>
        <button @click="fetchContadores" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Atualizar Contadores
        </button>
      </div>
      
      <input type="file" @change="handleFileChange" accept=".csv,.xlsx" />
      <button @click="uploadFile" :disabled="loading || !file">Enviar</button>
      <div v-if="loading">Processando...</div>
      <div v-if="error" style="color: red;">{{ error }}</div>
      
      <!-- Resumo estatístico -->
      <div v-if="produtos.length" style="margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
        <h3 style="margin-top: 0; color: #333;">Resumo das Sugestões</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
          <div style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 1.5rem; font-weight: bold; color: #42b883;">
              {{ (produtos.reduce((sum, p) => sum + p.confiabilidade, 0) / produtos.length).toFixed(1) }}%
            </div>
            <div style="color: #666;">Confiabilidade Média</div>
          </div>
          <div style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 1.5rem; font-weight: bold; color: #28a745;">
              {{ produtos.filter(p => p.padrao === 'TMPV').length }}
            </div>
            <div style="color: #666;">Padrão TMPV</div>
          </div>
          <div style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 1.5rem; font-weight: bold; color: #ffc107;">
              {{ produtos.filter(p => p.padrao === 'TMV').length }}
            </div>
            <div style="color: #666;">Padrão TMV</div>
          </div>
          <div style="text-align: center; padding: 1rem; background: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 1.5rem; font-weight: bold; color: #dc3545;">
              {{ produtos.filter(p => p.confiabilidade < 50).length }}
            </div>
            <div style="color: #666;">Baixa Confiabilidade (&lt;50%)</div>
          </div>
        </div>
        
        <!-- Filtro por confiabilidade -->
        <div style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 6px;">
          <h4 style="margin-top: 0; color: #333;">Filtrar por Confiabilidade</h4>
          <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
            <label style="display: flex; align-items: center; gap: 0.5rem;">
              <input type="radio" v-model="filtroConfiabilidade" value="todos" @change="filtrarPorConfiabilidade" />
              Todos ({{ produtos.length }})
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem;">
              <input type="radio" v-model="filtroConfiabilidade" value="alta" @change="filtrarPorConfiabilidade" />
              Alta (≥75%) ({{ produtos.filter(p => p.confiabilidade >= 75).length }})
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem;">
              <input type="radio" v-model="filtroConfiabilidade" value="media" @change="filtrarPorConfiabilidade" />
              Média (50-74%) ({{ produtos.filter(p => p.confiabilidade >= 50 && p.confiabilidade < 75).length }})
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem;">
              <input type="radio" v-model="filtroConfiabilidade" value="baixa" @change="filtrarPorConfiabilidade" />
              Baixa (&lt;50%) ({{ produtos.filter(p => p.confiabilidade < 50).length }})
            </label>
          </div>
        </div>
      </div>
      
      <table v-if="produtosFiltrados.length" border="1" cellpadding="8" style="margin-top: 2rem; width: 100%;">
        <thead>
          <tr>
            <th>Nome Original</th>
            <th>EAN</th>
            <th>Tipo</th>
            <th>Marca</th>
            <th>Particularidade</th>
            <th>Volume</th>
            <th>Padrão</th>
            <th>Confiabilidade</th>
            <th>Sugestão TMPV</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in produtosFiltrados" :key="i">
            <td>{{ p.nome_original }}</td>
            <td>{{ p.ean }}</td>
            <td>{{ p.tipo }}</td>
            <td>{{ p.marca }}</td>
            <td>
              <div>
                {{ p.particularidade }}
                <!-- Sugestões de particularidades -->
                <div v-if="p.sugestoes_particularidades && p.sugestoes_particularidades.length > 0" 
                     style="margin-top: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #007bff;">
                  <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">
                    💡 Sugestões para TMPV:
                  </div>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                    <button 
                      v-for="sugestao in p.sugestoes_particularidades" 
                      :key="sugestao"
                      @click="aceitarParticularidade(sugestao, i)"
                      style="
                        padding: 0.2rem 0.5rem;
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 0.7rem;
                        cursor: pointer;
                        transition: background 0.2s;
                      "
                      :disabled="loadingParticularidade === sugestao"
                      @mouseover="$event.target.style.background = '#0056b3'"
                      @mouseleave="$event.target.style.background = '#007bff'"
                    >
                      {{ sugestao }}
                      <span v-if="loadingParticularidade === sugestao">...</span>
                    </button>
                  </div>
                </div>
              </div>
            </td>
            <td>{{ p.volume }}</td>
            <td>
              <span :style="{ 
                padding: '0.2rem 0.5rem', 
                borderRadius: '4px', 
                fontSize: '0.8rem',
                fontWeight: 'bold',
                backgroundColor: p.padrao === 'TMPV' ? '#28a745' : '#ffc107',
                color: p.padrao === 'TMPV' ? 'white' : 'black'
              }">
                {{ p.padrao }}
              </span>
            </td>
            <td>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 60px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                  <div :style="{ 
                    width: p.confiabilidade + '%', 
                    height: '100%', 
                    backgroundColor: p.confiabilidade >= 75 ? '#28a745' : p.confiabilidade >= 50 ? '#ffc107' : '#dc3545',
                    transition: 'width 0.3s ease'
                  }"></div>
                </div>
                <span :style="{ 
                  fontSize: '0.9rem',
                  fontWeight: 'bold',
                  color: p.confiabilidade >= 75 ? '#28a745' : p.confiabilidade >= 50 ? '#856404' : '#dc3545'
                }">
                  {{ p.confiabilidade }}%
                </span>
                <!-- Tooltip com detalhes da confiabilidade -->
                <div v-if="p.detalhes_confiabilidade" 
                     style="position: relative; cursor: help; margin-left: 0.5rem;">
                  <span @click="toggleTooltip($event, i)" 
                        style="font-size: 0.8rem; color: #666; cursor: pointer;">ℹ️</span>
                  <div v-show="p.showTooltip" 
                       style="
                    position: absolute; 
                    bottom: 100%; 
                    left: 50%; 
                    transform: translateX(-50%);
                    background: #333; 
                    color: white; 
                    padding: 0.5rem; 
                    border-radius: 4px; 
                    font-size: 0.7rem; 
                    white-space: nowrap; 
                    z-index: 1000;
                    min-width: 200px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    margin-bottom: 5px;
                  ">
                    <div><strong>Detalhes da Confiabilidade:</strong></div>
                    <div>Base: {{ p.detalhes_confiabilidade.base }}%</div>
                    <div>Caracteres: {{ p.detalhes_confiabilidade.fator_chars }} ({{ p.detalhes_confiabilidade.razao_chars }})</div>
                    <div>Palavras perdidas: {{ p.detalhes_confiabilidade.fator_palavras_perdidas }}</div>
                    <div>Palavras adicionadas: {{ p.detalhes_confiabilidade.fator_palavras_adicionadas }}</div>
                    <div>Cobertura: {{ p.detalhes_confiabilidade.fator_cobertura }} ({{ p.detalhes_confiabilidade.cobertura_percentual }}%)</div>
                    <div>Estrutura: {{ p.detalhes_confiabilidade.fator_estrutura }}</div>
                    <div v-if="p.detalhes_confiabilidade.palavras_importantes_perdidas && p.detalhes_confiabilidade.palavras_importantes_perdidas.length > 0">
                      <strong>Importantes perdidas:</strong> {{ p.detalhes_confiabilidade.palavras_importantes_perdidas.join(', ') }}
                    </div>
                    <div v-if="p.detalhes_confiabilidade.palavras_adicionadas.length > 0">
                      <strong>Adicionadas:</strong> {{ p.detalhes_confiabilidade.palavras_adicionadas.join(', ') }}
                    </div>
                  </div>
                </div>
              </div>
            </td>
            <td><b>{{ p.sugestao_tmpv }}</b></td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="produtos.length && !produtosFiltrados.length" style="margin-top: 2rem; padding: 2rem; text-align: center; background: #f8f9fa; border-radius: 8px; color: #666;">
        <h3>Nenhum produto encontrado com o filtro selecionado</h3>
        <p>Tente selecionar um filtro diferente ou verificar os critérios de confiabilidade.</p>
      </div>
    </div>
    <div v-else-if="route === 'marcas'">
      <MarcasParam />
    </div>
    <div v-else-if="route === 'tipos'">
      <TiposParam />
    </div>
    <div v-else-if="route === 'particularidades'">
      <ParticularidadesParam />
    </div>
    <div v-else-if="route === 'volumes'">
      <VolumesParam />
    </div>
    <div v-else-if="route === 'abreviacoes'">
      <AbreviacoesParam />
    </div>
  </div>
</template>

<style scoped>
button {
  margin-left: 1rem;
  padding: 0.5rem 1.2rem;
  background: #42b883;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
input[type="file"] {
  margin-right: 1rem;
}
table th, table td {
  text-align: left;
}
</style>
