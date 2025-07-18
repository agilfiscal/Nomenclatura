<script setup>
import { ref, onMounted } from 'vue'

const marcas = ref([])
const novaMarca = ref("")
const loading = ref(false)
const error = ref("")
const file = ref(null)
const novasMarcas = ref("")

const fetchMarcas = async () => {
  loading.value = true
  error.value = ""
  try {
    const res = await fetch('http://localhost:8000/marcas/')
    marcas.value = await res.json()
  } catch (e) {
    error.value = 'Erro ao buscar marcas.'
  } finally {
    loading.value = false
  }
}

const adicionarMarca = async () => {
  if (!novaMarca.value.trim()) return
  loading.value = true
  error.value = ""
  try {
    const params = new URLSearchParams()
    params.append('nome', novaMarca.value)
    await fetch('http://localhost:8000/marcas/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    })
    novaMarca.value = ""
    await fetchMarcas()
  } catch (e) {
    error.value = 'Erro ao adicionar marca.'
  } finally {
    loading.value = false
  }
}

const adicionarMarcas = async () => {
  const linhas = novasMarcas.value.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (!linhas.length) return
  loading.value = true
  error.value = ""
  try {
    let adicionados = 0
    let ja_existiam = 0
    
    for (const marca of linhas) {
      const params = new URLSearchParams()
      params.append('nome', marca)
      const res = await fetch('http://localhost:8000/marcas/', {
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
    novasMarcas.value = ""
    await fetchMarcas()
    
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
    error.value = 'Erro ao adicionar marcas.'
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
    const res = await fetch('http://localhost:8000/marcas/importar/', {
      method: 'POST',
      body: formData
    })
    const resultado = await res.json()
    file.value = null
    await fetchMarcas()
    
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
    error.value = 'Erro ao importar marcas.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchMarcas)
</script>

<template>
  <div>
    <h2>Parametrização de Marcas</h2>
    <div style="margin-bottom: 1rem;">
      <input type="file" @change="handleFileChange" accept=".txt" />
      <button @click="uploadTXT" :disabled="loading || !file">Importar TXT</button>
    </div>
    <div style="margin-bottom: 1rem;">
      <textarea v-model="novasMarcas" placeholder="Digite uma marca por linha" rows="3" style="width: 300px; resize: vertical;"></textarea>
      <br />
      <button @click="adicionarMarcas" :disabled="loading || !novasMarcas">Adicionar</button>
    </div>
    <div v-if="error" style="color: red;">{{ error }}</div>
    <div v-if="loading">Carregando...</div>
    <div v-if="marcas.length && !loading" style="margin-top: 2rem; text-align: center;">
      <h3>Marcas cadastradas ({{ marcas.length }})</h3>
      <div class="marcas-lista">
        <span v-for="(m, i) in marcas" :key="i" class="marca-item">{{ m }}</span>
      </div>
    </div>
    <div v-else-if="!loading">Nenhuma marca cadastrada.</div>
  </div>
</template>

<style scoped>
input[type="file"] {
  margin-right: 1rem;
}
input[placeholder] {
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
.marcas-lista {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  justify-content: center;
  margin-top: 1rem;
}
.marca-item {
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