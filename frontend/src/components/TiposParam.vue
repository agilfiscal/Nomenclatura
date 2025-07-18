<script setup>
import { ref, onMounted } from 'vue'

const tipos = ref([])
const novosTipos = ref("")
const loading = ref(false)
const error = ref("")
const file = ref(null)

const fetchTipos = async () => {
  loading.value = true
  error.value = ""
  try {
    const res = await fetch('http://localhost:8000/tipos/')
    tipos.value = await res.json()
  } catch (e) {
    error.value = 'Erro ao buscar tipos.'
  } finally {
    loading.value = false
  }
}

const adicionarTipos = async () => {
  const linhas = novosTipos.value.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (!linhas.length) return
  loading.value = true
  error.value = ""
  try {
    let adicionados = 0
    let ja_existiam = 0
    
    for (const tipo of linhas) {
      const params = new URLSearchParams()
      params.append('nome', tipo)
      const res = await fetch('http://localhost:8000/tipos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
      })
      const resultado = await res.json()
      if (resultado.status === 'adicionado') {
        adicionados++
      } else {
        ja_existiam++
      }
    }
    novosTipos.value = ""
    await fetchTipos()
    
    // Mostrar feedback sobre o resultado
    if (adicionados > 0 || ja_existiam > 0) {
      let mensagem = `Processados ${linhas.length} itens. `
      if (adicionados > 0) {
        mensagem += `${adicionados} adicionados. `
      }
      if (ja_existiam > 0) {
        mensagem += `${ja_existiam} já existiam (ignorados).`
      }
      alert(mensagem)
    }
  } catch (e) {
    error.value = 'Erro ao adicionar tipos.'
  } finally {
    loading.value = false
  }
}

const handleFileChange = (e) => {
  file.value = e.target.files[0]
}

const uploadTXT = async () => {
  if (!file.value) return
  loading.value = true
  error.value = ""
  const formData = new FormData()
  formData.append('file', file.value)
  try {
    const res = await fetch('http://localhost:8000/tipos/importar/', {
      method: 'POST',
      body: formData
    })
    const resultado = await res.json()
    file.value = null
    await fetchTipos()
    
    // Mostrar feedback sobre o resultado
    if (resultado.adicionados.length > 0 || resultado.ja_existiam.length > 0) {
      let mensagem = `Processados ${resultado.total_processados} itens. `
      if (resultado.adicionados.length > 0) {
        mensagem += `${resultado.adicionados.length} adicionados. `
      }
      if (resultado.ja_existiam.length > 0) {
        mensagem += `${resultado.ja_existiam.length} já existiam (ignorados).`
      }
      alert(mensagem)
    }
  } catch (e) {
    error.value = 'Erro ao importar tipos.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchTipos)
</script>

<template>
  <div>
    <h2>Parametrização de Tipos</h2>
    <div style="margin-bottom: 1rem;">
      <input type="file" @change="handleFileChange" accept=".txt" />
      <button @click="uploadTXT" :disabled="loading || !file">Importar TXT</button>
    </div>
    <div style="margin-bottom: 1rem;">
      <textarea v-model="novosTipos" placeholder="Digite um tipo por linha" rows="3" style="width: 300px; resize: vertical;"></textarea>
      <br />
      <button @click="adicionarTipos" :disabled="loading || !novosTipos">Adicionar</button>
    </div>
    <div v-if="error" style="color: red;">{{ error }}</div>
    <div v-if="loading">Carregando...</div>
    <div v-if="tipos.length && !loading" style="margin-top: 2rem; text-align: center;">
      <h3>Tipos cadastrados ({{ tipos.length }})</h3>
      <div class="tipos-lista">
        <span v-for="(t, i) in tipos" :key="i" class="tipo-item">{{ t }}</span>
      </div>
    </div>
    <div v-else-if="!loading">Nenhum tipo cadastrado.</div>
  </div>
</template>

<style scoped>
input[type="file"] {
  margin-right: 1rem;
}
textarea {
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  border: 1px solid #ccc;
  margin-right: 0.5rem;
}
button {
  padding: 0.3rem 1rem;
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
.tipos-lista {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  justify-content: center;
  margin-top: 1rem;
}
.tipo-item {
  background: #e6f7f1;
  color: #222;
  padding: 0.5rem 1.2rem;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  display: inline-block;
}
</style> 