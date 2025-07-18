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
const loading = ref(false)
const error = ref("")

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
      // Usar diretamente os campos que o backend retorna
      produtos.value = data.produtos
    }
  } catch (err) {
    error.value = 'Erro ao enviar arquivo.'
  } finally {
    loading.value = false
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
      <table v-if="produtos.length" border="1" cellpadding="8" style="margin-top: 2rem; width: 100%;">
        <thead>
          <tr>
            <th>Nome Original</th>
            <th>EAN</th>
            <th>Tipo</th>
            <th>Marca</th>
            <th>Particularidade</th>
            <th>Volume</th>
            <th>Sugestão TMPV</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in produtos" :key="i">
            <td>{{ p.nome_original }}</td>
            <td>{{ p.ean }}</td>
            <td>{{ p.tipo }}</td>
            <td>{{ p.marca }}</td>
            <td>{{ p.particularidade }}</td>
            <td>{{ p.volume }}</td>
            <td><b>{{ p.sugestao_tmpv }}</b></td>
          </tr>
        </tbody>
      </table>
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
