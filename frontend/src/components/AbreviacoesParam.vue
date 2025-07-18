<script setup>
import { ref, onMounted } from 'vue'

const abreviacoes = ref([])
const novaAbreviacao = ref("")
const novaPalavraCompleta = ref("")
const loading = ref(false)
const error = ref("")
const success = ref("")

const fetchAbreviacoes = async () => {
  loading.value = true
  error.value = ""
  try {
    const res = await fetch('http://localhost:8000/abreviacoes/')
    abreviacoes.value = await res.json()
  } catch (e) {
    error.value = 'Erro ao buscar abreviações.'
  } finally {
    loading.value = false
  }
}

const adicionarAbreviacao = async () => {
  if (!novaAbreviacao.value.trim() || !novaPalavraCompleta.value.trim()) {
    error.value = 'Preencha ambos os campos.'
    return
  }
  
  loading.value = true
  error.value = ""
  success.value = ""
  
  try {
    const params = new URLSearchParams()
    params.append('abreviacao', novaAbreviacao.value)
    params.append('palavra_completa', novaPalavraCompleta.value)
    
    const res = await fetch('http://localhost:8000/abreviacoes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    })
    
    const resultado = await res.json()
    
    if (resultado.status === 'adicionado') {
      success.value = 'Abreviação adicionada com sucesso!'
      novaAbreviacao.value = ""
      novaPalavraCompleta.value = ""
      await fetchAbreviacoes()
    } else if (resultado.status === 'já_existia') {
      error.value = 'Esta abreviação já existe.'
    } else {
      error.value = resultado.mensagem || 'Erro ao adicionar abreviação.'
    }
  } catch (e) {
    error.value = 'Erro ao adicionar abreviação.'
  } finally {
    loading.value = false
  }
}

const removerAbreviacao = async (id) => {
  if (!confirm('Tem certeza que deseja remover esta abreviação?')) return
  
  loading.value = true
  error.value = ""
  success.value = ""
  
  try {
    const res = await fetch(`http://localhost:8000/abreviacoes/${id}`, {
      method: 'DELETE'
    })
    
    const resultado = await res.json()
    
    if (resultado.status === 'removido') {
      success.value = 'Abreviação removida com sucesso!'
      await fetchAbreviacoes()
    } else {
      error.value = resultado.mensagem || 'Erro ao remover abreviação.'
    }
  } catch (e) {
    error.value = 'Erro ao remover abreviação.'
  } finally {
    loading.value = false
  }
}

const inicializarAbreviacoes = async () => {
  if (!confirm('Deseja adicionar abreviações padrão comuns? Isso não substituirá abreviações existentes.')) return
  
  loading.value = true
  error.value = ""
  success.value = ""
  
  try {
    const res = await fetch('http://localhost:8000/abreviacoes/inicializar/', {
      method: 'POST'
    })
    
    const resultado = await res.json()
    
    if (resultado.adicionadas > 0 || resultado.ja_existiam > 0) {
      let mensagem = `Processadas ${resultado.total_processadas} abreviações. `
      if (resultado.adicionadas > 0) {
        mensagem += `${resultado.adicionadas} adicionadas. `
      }
      if (resultado.ja_existiam > 0) {
        mensagem += `${resultado.ja_existiam} já existiam (ignoradas).`
      }
      success.value = mensagem
      await fetchAbreviacoes()
    } else {
      error.value = 'Erro ao inicializar abreviações.'
    }
  } catch (e) {
    error.value = 'Erro ao inicializar abreviações.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchAbreviacoes)
</script>

<template>
  <div>
    <h2>Gerenciamento de Abreviações</h2>
    
    <!-- Formulário para adicionar abreviação -->
    <div style="margin-bottom: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
      <h3 style="margin-top: 0;">Adicionar Nova Abreviação</h3>
      <div style="display: flex; gap: 1rem; align-items: end; flex-wrap: wrap;">
        <div>
          <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Abreviação:</label>
          <input 
            v-model="novaAbreviacao" 
            placeholder="Ex: CERV" 
            style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; width: 150px;"
          />
        </div>
        <div>
          <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Palavra Completa:</label>
          <input 
            v-model="novaPalavraCompleta" 
            placeholder="Ex: CERVEJA" 
            style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; width: 150px;"
          />
        </div>
        <button 
          @click="adicionarAbreviacao" 
          :disabled="loading || !novaAbreviacao || !novaPalavraCompleta"
          style="padding: 0.5rem 1rem; background: #42b883; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          Adicionar
        </button>
      </div>
      <div style="margin-top: 1rem;">
        <button 
          @click="inicializarAbreviacoes" 
          :disabled="loading"
          style="padding: 0.5rem 1rem; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          Inicializar com Abreviações Padrão
        </button>
      </div>
    </div>
    
    <!-- Mensagens de feedback -->
    <div v-if="error" style="color: red; margin-bottom: 1rem; padding: 0.5rem; background: #ffe6e6; border-radius: 4px;">{{ error }}</div>
    <div v-if="success" style="color: green; margin-bottom: 1rem; padding: 0.5rem; background: #e6ffe6; border-radius: 4px;">{{ success }}</div>
    
    <!-- Lista de abreviações -->
    <div v-if="loading">Carregando...</div>
    <div v-else-if="abreviacoes.length" style="margin-top: 2rem;">
      <h3>Abreviações cadastradas ({{ abreviacoes.length }})</h3>
      <div class="abreviacoes-lista">
        <div 
          v-for="(abrev, i) in abreviacoes" 
          :key="i" 
          class="abreviacao-item"
          style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: white; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 0.5rem;"
        >
          <div>
            <span style="font-weight: bold; color: #42b883;">{{ abrev.abreviacao }}</span>
            <span style="margin: 0 0.5rem;">→</span>
            <span style="color: #666;">{{ abrev.palavra_completa }}</span>
          </div>
          <button 
            @click="removerAbreviacao(abrev.id)" 
            style="padding: 0.3rem 0.8rem; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem;"
          >
            Remover
          </button>
        </div>
      </div>
    </div>
    <div v-else style="text-align: center; color: #666; margin-top: 2rem;">
      Nenhuma abreviação cadastrada.
    </div>
    
    <!-- Exemplos de uso -->
    <div style="margin-top: 2rem; padding: 1rem; background: #e6f7f1; border-radius: 8px;">
      <h3 style="margin-top: 0; color: #333;">Como Funciona</h3>
      <p style="margin-bottom: 0.5rem;">O sistema automaticamente expande abreviações antes de processar os nomes dos produtos.</p>
      <p style="margin-bottom: 0.5rem;"><strong>Exemplos:</strong></p>
      <ul style="margin: 0; padding-left: 1.5rem;">
        <li>"CERV" → "CERVEJA"</li>
        <li>"C/" → "COM"</li>
        <li>"REFRIG" → "REFRIGERANTE"</li>
        <li>"CHOC" → "CHOCOLATE"</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
button:disabled {
  background: #ccc !important;
  cursor: not-allowed;
}

.abreviacoes-lista {
  max-height: 400px;
  overflow-y: auto;
}
</style> 