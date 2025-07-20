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
const loadingTipo = ref("")
const loadingMarca = ref("")
const loadingVolume = ref("")

// Variáveis para notificações toast
const notificacoes = ref([])
const proximoId = ref(1)

// Variáveis para ordenação da tabela
const ordenacao = ref({
  campo: null,
  direcao: 'asc' // 'asc' ou 'desc'
})

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
      
      // Aplicar ordenação padrão por confiabilidade (maior primeiro)
      ordenacao.value.campo = 'confiabilidade'
      ordenacao.value.direcao = 'desc'
      ordenarProdutos('confiabilidade')
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

// Função para ordenar produtos
const ordenarProdutos = (campo) => {
  // Se clicar no mesmo campo, alternar direção
  if (ordenacao.value.campo === campo) {
    ordenacao.value.direcao = ordenacao.value.direcao === 'asc' ? 'desc' : 'asc'
  } else {
    // Se clicar em campo diferente, definir como ascendente
    ordenacao.value.campo = campo
    ordenacao.value.direcao = 'asc'
  }
  
  // Aplicar ordenação
  produtosFiltrados.value.sort((a, b) => {
    let valorA, valorB
    
    switch (campo) {
      case 'nome_original':
        valorA = a.nome_original.toLowerCase()
        valorB = b.nome_original.toLowerCase()
        break
      case 'confiabilidade':
        valorA = a.confiabilidade
        valorB = b.confiabilidade
        break
      case 'sugestao_tmpv':
        valorA = a.sugestao_tmpv.toLowerCase()
        valorB = b.sugestao_tmpv.toLowerCase()
        break
      default:
        return 0
    }
    
    // Comparar valores
    if (valorA < valorB) {
      return ordenacao.value.direcao === 'asc' ? -1 : 1
    }
    if (valorA > valorB) {
      return ordenacao.value.direcao === 'asc' ? 1 : -1
    }
    return 0
  })
}

// Função para adicionar notificação toast
const adicionarNotificacao = (mensagem, tipo = 'sucesso') => {
  const id = proximoId.value++
  const notificacao = {
    id,
    mensagem,
    tipo,
    timestamp: Date.now()
  }
  
  notificacoes.value.push(notificacao)
  
  // Remover notificação após 3 segundos
  setTimeout(() => {
    removerNotificacao(id)
  }, 3000)
}

// Função para remover notificação
const removerNotificacao = (id) => {
  const index = notificacoes.value.findIndex(n => n.id === id)
  if (index > -1) {
    notificacoes.value.splice(index, 1)
  }
}

// Função para obter ícone de ordenação
const getIconeOrdenacao = (campo) => {
  if (ordenacao.value.campo !== campo) {
    return '↕️' // Neutro
  }
  return ordenacao.value.direcao === 'asc' ? '↑' : '↓'
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
  
  // Aplicar ordenação atual após filtrar
  if (ordenacao.value.campo) {
    ordenarProdutos(ordenacao.value.campo)
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
      
      adicionarNotificacao(`✅ Particularidade "${particularidade}" cadastrada com sucesso!`, 'sucesso')
    } else if (result.status === 'já_existia') {
      adicionarNotificacao(`ℹ️ A particularidade "${particularidade}" já existe no banco de dados.`, 'info')
    } else {
      adicionarNotificacao(`❌ Erro: ${result.mensagem}`, 'erro')
    }
  } catch (error) {
    console.error('Erro ao cadastrar particularidade:', error)
    adicionarNotificacao('❌ Erro ao cadastrar particularidade. Tente novamente.', 'erro')
  } finally {
    loadingParticularidade.value = ""
  }
}

// Função para aceitar um tipo sugerido
const aceitarTipo = async (tipo, indexProduto) => {
  loadingTipo.value = tipo
  
  try {
    const formData = new FormData()
    formData.append('nome', tipo)
    
    const response = await fetch('http://localhost:8000/tipos/sugerir/', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (result.status === 'adicionado') {
      // Atualizar o produto localmente
      const produto = produtosFiltrados.value[indexProduto]
      produto.tipo = tipo
      produto.sugestoes_tipos = produto.sugestoes_tipos.filter(t => t !== tipo)
      
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
      
      adicionarNotificacao(`✅ Tipo "${tipo}" cadastrado com sucesso!`, 'sucesso')
    } else if (result.status === 'já_existia') {
      adicionarNotificacao(`ℹ️ O tipo "${tipo}" já existe no banco de dados.`, 'info')
    } else {
      adicionarNotificacao(`❌ Erro: ${result.mensagem}`, 'erro')
    }
  } catch (error) {
    console.error('Erro ao cadastrar tipo:', error)
    adicionarNotificacao('❌ Erro ao cadastrar tipo. Tente novamente.', 'erro')
  } finally {
    loadingTipo.value = ""
  }
}

// Função para aceitar uma marca sugerida
const aceitarMarca = async (marca, indexProduto) => {
  loadingMarca.value = marca
  
  try {
    const formData = new FormData()
    formData.append('nome', marca)
    
    const response = await fetch('http://localhost:8000/marcas/sugerir/', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (result.status === 'adicionado') {
      // Atualizar o produto localmente
      const produto = produtosFiltrados.value[indexProduto]
      produto.marca = marca
      produto.sugestoes_marcas = produto.sugestoes_marcas.filter(m => m !== marca)
      
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
      
      adicionarNotificacao(`✅ Marca "${marca}" cadastrada com sucesso!`, 'sucesso')
    } else if (result.status === 'já_existia') {
      adicionarNotificacao(`ℹ️ A marca "${marca}" já existe no banco de dados.`, 'info')
    } else {
      adicionarNotificacao(`❌ Erro: ${result.mensagem}`, 'erro')
    }
  } catch (error) {
    console.error('Erro ao cadastrar marca:', error)
    adicionarNotificacao('❌ Erro ao cadastrar marca. Tente novamente.', 'erro')
  } finally {
    loadingMarca.value = ""
  }
}

// Função para aceitar um volume sugerido
const aceitarVolume = async (volume, indexProduto) => {
  loadingVolume.value = volume
  
  try {
    const formData = new FormData()
    formData.append('nome', volume)
    
    const response = await fetch('http://localhost:8000/volumes/sugerir/', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (result.status === 'adicionado') {
      // Atualizar o produto localmente
      const produto = produtosFiltrados.value[indexProduto]
      produto.volume = volume
      produto.sugestoes_volumes = produto.sugestoes_volumes.filter(v => v !== volume)
      
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
      
      adicionarNotificacao(`✅ Volume "${volume}" cadastrado com sucesso!`, 'sucesso')
    } else if (result.status === 'já_existia') {
      adicionarNotificacao(`ℹ️ O volume "${volume}" já existe no banco de dados.`, 'info')
    } else {
      adicionarNotificacao(`❌ Erro: ${result.mensagem}`, 'erro')
    }
  } catch (error) {
    console.error('Erro ao cadastrar volume:', error)
    adicionarNotificacao('❌ Erro ao cadastrar volume. Tente novamente.', 'erro')
  } finally {
    loadingVolume.value = ""
  }
}

// Buscar contadores quando o componente for montado
onMounted(() => {
  fetchContadores()
})
</script>

<template>
  <!-- Sistema de Notificações Toast -->
  <div class="toast-container" style="
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 10px;
  ">
    <div 
      v-for="notificacao in notificacoes" 
      :key="notificacao.id"
      :style="{
        padding: '12px 16px',
        borderRadius: '6px',
        color: 'white',
        fontSize: '14px',
        fontWeight: '500',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        transform: 'translateX(0)',
        transition: 'all 0.3s ease',
        backgroundColor: notificacao.tipo === 'sucesso' ? '#28a745' : 
                        notificacao.tipo === 'erro' ? '#dc3545' : 
                        notificacao.tipo === 'info' ? '#17a2b8' : '#6c757d',
        borderLeft: `4px solid ${
          notificacao.tipo === 'sucesso' ? '#1e7e34' : 
          notificacao.tipo === 'erro' ? '#c82333' : 
          notificacao.tipo === 'info' ? '#138496' : '#545b62'
        }`
      }"
      @click="removerNotificacao(notificacao.id)"
      style="cursor: pointer;"
    >
      {{ notificacao.mensagem }}
    </div>
  </div>

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
      
      <!-- Indicador de ordenação atual -->
      <div v-if="ordenacao.campo && produtosFiltrados.length" 
           style="margin: 1rem 0; padding: 0.5rem 1rem; background: #e3f2fd; border-radius: 4px; border-left: 4px solid #2196f3;">
        <span style="font-size: 0.9rem; color: #1976d2;">
          📊 Ordenado por: <strong>{{ 
            ordenacao.campo === 'nome_original' ? 'Nome Original' : 
            ordenacao.campo === 'confiabilidade' ? 'Confiabilidade' : 
            ordenacao.campo === 'sugestao_tmpv' ? 'Sugestão TMPV' : '' 
          }}</strong> 
          ({{ ordenacao.direcao === 'asc' ? 'Crescente' : 'Decrescente' }})
        </span>
      </div>
      
      <table v-if="produtosFiltrados.length" border="1" cellpadding="8" style="margin-top: 2rem; width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th @click="ordenarProdutos('nome_original')" 
                style="cursor: pointer; user-select: none; transition: all 0.2s; padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;"
                @mouseover="$event.target.style.backgroundColor = '#e9ecef'"
                @mouseleave="$event.target.style.backgroundColor = ordenacao.campo === 'nome_original' ? '#d4edda' : '#f8f9fa'">
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>Nome Original</span>
                <span style="font-size: 1.2rem;">{{ getIconeOrdenacao('nome_original') }}</span>
              </div>
            </th>
            <th style="padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;">EAN</th>
            <th style="padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;">Tipo</th>
            <th style="padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;">Marca</th>
            <th style="padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;">Particularidade</th>
            <th style="padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;">Volume</th>
            <th style="padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;">Padrão</th>
            <th @click="ordenarProdutos('confiabilidade')" 
                style="cursor: pointer; user-select: none; transition: all 0.2s; padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;"
                @mouseover="$event.target.style.backgroundColor = '#e9ecef'"
                @mouseleave="$event.target.style.backgroundColor = ordenacao.campo === 'confiabilidade' ? '#d4edda' : '#f8f9fa'">
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>Confiabilidade</span>
                <span style="font-size: 1.2rem;">{{ getIconeOrdenacao('confiabilidade') }}</span>
              </div>
            </th>
            <th @click="ordenarProdutos('sugestao_tmpv')" 
                style="cursor: pointer; user-select: none; transition: all 0.2s; padding: 12px 8px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;"
                @mouseover="$event.target.style.backgroundColor = '#e9ecef'"
                @mouseleave="$event.target.style.backgroundColor = ordenacao.campo === 'sugestao_tmpv' ? '#d4edda' : '#f8f9fa'">
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>Sugestão TMPV</span>
                <span style="font-size: 1.2rem;">{{ getIconeOrdenacao('sugestao_tmpv') }}</span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in produtosFiltrados" :key="i">
            <td>{{ p.nome_original }}</td>
            <td>{{ p.ean }}</td>
            <td>
              <div>
                {{ p.tipo }}
                <!-- Sugestões de tipos -->
                <div v-if="p.sugestoes_tipos && p.sugestoes_tipos.length > 0" 
                     style="margin-top: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #28a745;">
                  <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">
                    💡 Sugestões de Tipo:
                  </div>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                    <button 
                      v-for="sugestao in p.sugestoes_tipos" 
                      :key="sugestao"
                      @click="aceitarTipo(sugestao, i)"
                      style="
                        padding: 0.2rem 0.5rem;
                        background: #28a745;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 0.7rem;
                        cursor: pointer;
                        transition: background 0.2s;
                      "
                      :disabled="loadingTipo === sugestao"
                      @mouseover="$event.target.style.background = '#1e7e34'"
                      @mouseleave="$event.target.style.background = '#28a745'"
                    >
                      {{ sugestao }}
                      <span v-if="loadingTipo === sugestao">...</span>
                    </button>
                  </div>
                </div>
              </div>
            </td>
            <td>
              <div>
                {{ p.marca }}
                <!-- Sugestões de marcas -->
                <div v-if="p.sugestoes_marcas && p.sugestoes_marcas.length > 0" 
                     style="margin-top: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #ffc107;">
                  <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">
                    💡 Sugestões de Marca:
                  </div>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                    <button 
                      v-for="sugestao in p.sugestoes_marcas" 
                      :key="sugestao"
                      @click="aceitarMarca(sugestao, i)"
                      style="
                        padding: 0.2rem 0.5rem;
                        background: #ffc107;
                        color: black;
                        border: none;
                        border-radius: 3px;
                        font-size: 0.7rem;
                        cursor: pointer;
                        transition: background 0.2s;
                      "
                      :disabled="loadingMarca === sugestao"
                      @mouseover="$event.target.style.background = '#e0a800'"
                      @mouseleave="$event.target.style.background = '#ffc107'"
                    >
                      {{ sugestao }}
                      <span v-if="loadingMarca === sugestao">...</span>
                    </button>
                  </div>
                </div>
              </div>
            </td>
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
            <td>
              <div>
                {{ p.volume }}
                <!-- Sugestões de volumes -->
                <div v-if="p.sugestoes_volumes && p.sugestoes_volumes.length > 0" 
                     style="margin-top: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #dc3545;">
                  <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">
                    💡 Sugestões de Volume:
                  </div>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                    <button 
                      v-for="sugestao in p.sugestoes_volumes" 
                      :key="sugestao"
                      @click="aceitarVolume(sugestao, i)"
                      style="
                        padding: 0.2rem 0.5rem;
                        background: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 0.7rem;
                        cursor: pointer;
                        transition: background 0.2s;
                      "
                      :disabled="loadingVolume === sugestao"
                      @mouseover="$event.target.style.background = '#c82333'"
                      @mouseleave="$event.target.style.background = '#dc3545'"
                    >
                      {{ sugestao }}
                      <span v-if="loadingVolume === sugestao">...</span>
                    </button>
                  </div>
                </div>
              </div>
            </td>
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
