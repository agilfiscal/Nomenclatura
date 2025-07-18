<template>
  <nav class="navbar">
    <ul>
      <li :class="{active: route === 'padronizar'}" @click="$emit('navigate', 'padronizar')">Padronizar Nomes</li>
      <li :class="{active: route === 'marcas'}" @click="$emit('navigate', 'marcas')">Marcas</li>
      <li :class="{active: route === 'tipos'}" @click="$emit('navigate', 'tipos')">Tipos</li>
      <li :class="{active: route === 'particularidades'}" @click="$emit('navigate', 'particularidades')">Particularidades</li>
      <li :class="{active: route === 'volumes'}" @click="$emit('navigate', 'volumes')">Volumes</li>
      <li :class="{active: route === 'abreviacoes'}" @click="$emit('navigate', 'abreviacoes')">Abreviações</li>
    </ul>
  </nav>
</template>

<script setup>
import { defineProps } from 'vue'
const props = defineProps({ route: String })
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  z-index: 1000;
  background: #42b883;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  padding: 0.5rem 0;
  border-radius: 0 0 12px 12px;
}
.navbar ul {
  list-style: none;
  display: flex;
  gap: 2rem;
  margin: 0 auto;
  padding: 0;
  justify-content: center;
  max-width: 1100px;
}
.navbar li {
  color: #fff;
  cursor: pointer;
  font-weight: bold;
  padding: 0.3rem 1.2rem;
  border-radius: 4px;
  transition: background 0.2s;
  font-size: 1.1rem;
}
.navbar li.active, .navbar li:hover {
  background: #2c8c6b;
}
@media (max-width: 700px) {
  .navbar ul {
    gap: 0.5rem;
    font-size: 0.95rem;
  }
  .navbar li {
    padding: 0.3rem 0.7rem;
    font-size: 0.98rem;
  }
}
</style> 