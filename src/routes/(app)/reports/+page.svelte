<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/config';
  import { fade, slide } from 'svelte/transition';

  let rawItems = $state([]);
  let loading = $state(true);
  let error = $state('');

  // Filters
  let startDate = $state('');
  let endDate = $state('');
  let selectedType = $state('TODOS');

  const tiposResiduo = ['TODOS', 'PELIGROSO', 'NO PELIGROSO', 'NFU', 'RAEE', 'ESPECIAL', 'OTROS'];

  onMount(fetchData);

  async function fetchData() {
    loading = true;
    error = '';
    try {
      const response = await fetch(`${API_BASE_URL}/waste/generation`);
      if (!response.ok) throw new Error('Error al cargar datos');
      rawItems = await response.json();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  // Derived Filtering Logic
  let filteredItems = $derived(rawItems.filter(item => {
    const itemDate = new Date(item.fecha_registro).toISOString().split('T')[0];
    
    const matchesDate = (!startDate || itemDate >= startDate) && 
                        (!endDate || itemDate <= endDate);
    
    const matchesType = selectedType === 'TODOS' || item.tipo_residuo === selectedType;
    
    return matchesDate && matchesType;
  }));

  // Stats
  let totalWeight = $derived(filteredItems.reduce((acc, item) => acc + (item.peso_total || 0), 0));
  let totalRecords = $derived(filteredItems.length);
  let dangerousCount = $derived(filteredItems.filter(i => i.tipo_residuo === 'PELIGROSO').length);

</script>

<Navbar title="Centro de Reportes e Informes" />

<div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8 pb-20">
  
  <!-- FILTERS SECTION -->
  <section class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
    <div class="flex flex-col md:flex-row gap-6 items-end">
      <div class="space-y-1.5 flex-1">
        <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Rango de Fecha Desde</label>
        <input type="date" bind:value={startDate} class="w-full h-11 rounded-xl border-gray-200 focus:border-scientific-400 transition-all px-4" />
      </div>
      <div class="space-y-1.5 flex-1">
        <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Hasta</label>
        <input type="date" bind:value={endDate} class="w-full h-11 rounded-xl border-gray-200 focus:border-scientific-400 transition-all px-4" />
      </div>
      <div class="space-y-1.5 flex-1">
        <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Tipo de Residuo</label>
        <select bind:value={selectedType} class="w-full h-11 rounded-xl border-gray-200 focus:border-scientific-400 transition-all px-4 bg-white">
          {#each tiposResiduo as t} <option value={t}>{t}</option> {/each}
        </select>
      </div>
      <button on:click={() => { startDate = ''; endDate = ''; selectedType = 'TODOS'; }} class="h-11 px-6 text-sm font-bold text-gray-500 hover:text-red-500 transition-colors">
        Limpiar
      </button>
    </div>
  </section>

  <!-- STATS GRID -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <div class="bg-gradient-to-br from-scientific-600 to-scientific-800 p-6 rounded-2xl text-white shadow-lg shadow-scientific-100">
      <span class="block text-xs font-bold uppercase opacity-80 mb-1">Masa Total Gestionada</span>
      <p class="text-3xl font-black">{totalWeight.toLocaleString()} <span class="text-lg font-normal">kg</span></p>
      <div class="mt-4 flex items-center gap-2 text-[10px] font-bold uppercase">
         <span class="bg-white/20 px-2 py-1 rounded">Basado en filtros actuales</span>
      </div>
    </div>
    
    <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
      <div>
        <span class="block text-xs font-bold uppercase text-gray-400 mb-1">Total Registros</span>
        <p class="text-3xl font-black text-gray-900">{totalRecords}</p>
      </div>
      <p class="text-[10px] text-gray-400 font-medium mt-2 italic">Representa el {totalRecords > 0 ? ((dangerousCount/totalRecords)*100).toFixed(0) : 0}% del histórico filtrado</p>
    </div>

    <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
      <div>
        <span class="block text-xs font-bold uppercase text-red-400 mb-1">Residuos Peligrosos</span>
        <p class="text-3xl font-black text-red-600">{dangerousCount}</p>
      </div>
      <div class="h-1 w-full bg-gray-100 rounded-full mt-3 overflow-hidden">
        <div class="h-full bg-red-500 transition-all duration-500" style="width: {totalRecords > 0 ? (dangerousCount/totalRecords)*100 : 0}%"></div>
      </div>
    </div>
  </div>

  <!-- DATA TABLE -->
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
    {#if loading}
      <div class="p-20 text-center">
        <svg class="animate-spin h-10 w-10 text-scientific-600 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-sm text-gray-400 font-bold mt-4">Generando consolidado...</p>
      </div>
    {:else if filteredItems.length === 0}
      <div class="p-20 text-center space-y-3">
        <div class="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto text-gray-300">
           <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
        </div>
        <p class="text-gray-400 font-medium">No hay registros para este rango de fecha o tipo.</p>
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-gray-50/50 border-b border-gray-100">
            <tr>
              <th class="px-6 py-4 text-[10px] font-black uppercase text-gray-400 tracking-widest">Fecha</th>
              <th class="px-6 py-4 text-[10px] font-black uppercase text-gray-400 tracking-widest">Responsable / Unidad</th>
              <th class="px-6 py-4 text-[10px] font-black uppercase text-gray-400 tracking-widest">Residuo</th>
              <th class="px-6 py-4 text-[10px] font-black uppercase text-gray-400 tracking-widest text-center">Tipo</th>
              <th class="px-6 py-4 text-[10px] font-black uppercase text-gray-400 tracking-widest text-right">Peso (kg)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each filteredItems as item}
              <tr class="hover:bg-scientific-50/10 transition-colors">
                <td class="px-6 py-4 text-sm text-gray-500 font-medium">{new Date(item.fecha_registro).toLocaleDateString()}</td>
                <td class="px-6 py-4">
                  <p class="text-sm font-bold text-gray-900 leading-none">{item.responsable}</p>
                  <p class="text-[10px] text-gray-400 uppercase font-medium mt-1">{item.unidad_generadora}</p>
                </td>
                <td class="px-6 py-4">
                  <p class="text-sm text-gray-600 font-medium line-clamp-1">{item.caracteristica}</p>
                  {#if item.analysis_material_name}
                    <span class="text-[9px] font-bold text-indigo-500 uppercase tracking-tighter">IA: {item.analysis_material_name}</span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-center">
                  <span class="inline-block px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter {item.tipo_residuo === 'PELIGROSO' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}">
                    {item.tipo_residuo}
                  </span>
                </td>
                <td class="px-6 py-4 text-right">
                  <p class="text-sm font-black text-gray-900">{item.peso_total.toFixed(2)}</p>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

</div>
