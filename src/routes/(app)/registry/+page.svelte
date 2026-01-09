<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/config';

  let wasteItems = $state([]);
  let loading = $state(true);
  let error = $state('');

  onMount(fetchWasteItems);

  async function fetchWasteItems() {
    loading = true;
    error = '';
    try {
      const response = await fetch(`${API_BASE_URL}/waste/generation`);
      if (!response.ok) throw new Error('No se pudieron cargar los registros');
      
      const data = await response.json();
      
      // Map backend Residuo model to frontend structure
      wasteItems = data.map((item: any) => ({
        id: item.id,
        fecha: new Date(item.fecha_registro).toLocaleDateString(),
        responsable: item.responsable,
        unidad: item.unidad_generadora,
        name: item.caracteristica,
        type: item.tipo_residuo,
        cantidad: `${item.cantidad} ${item.unidad_medida}`,
        peso: `${item.peso_total} kg`,
        category: item.tipo_residuo === 'PELIGRO' ? 'Peligroso' : 'No Peligroso'
      }));
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  let searchQuery = $state('');

  let filteredItems = $derived(wasteItems.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    item.responsable.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.unidad.toLowerCase().includes(searchQuery.toLowerCase())
  ));

</script>

<Navbar title="Registros Maestros de Residuos" />

<div class="p-6 md:p-8 space-y-6">
  <!-- Actions Bar -->
  <div class="flex flex-col md:flex-row justify-between gap-4">
    <div class="relative w-full md:w-96">
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
        </svg>
      </div>
      <input 
        type="text" 
        bind:value={searchQuery}
        class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:border-scientific-500 focus:ring-1 focus:ring-scientific-500 sm:text-sm transition-shadow"
        placeholder="Buscar por descripción, responsable..."
      />
    </div>
    <a href="/waste-generation" class="bg-scientific-600 hover:bg-scientific-700 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
      Nuevo Registro
    </a>
  </div>

  <!-- Data Grid -->
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    {#if loading}
      <div class="p-12 text-center text-gray-500">
        <svg class="animate-spin h-8 w-8 mx-auto mb-4 text-scientific-600" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Cargando registros...
      </div>
    {:else if error}
      <div class="p-12 text-center text-red-500">
        <p class="mb-4">{error}</p>
        <button on:click={fetchWasteItems} class="text-scientific-600 font-bold underline">Reintentar</button>
      </div>
    {:else if filteredItems.length === 0}
      <div class="p-12 text-center text-gray-500">
        No se encontraron registros.
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Responsable</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unidad</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clase</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            {#each filteredItems as item}
              <tr class="hover:bg-gray-50 transition-colors group">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.fecha}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.responsable}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.unidad}</td>
                <td class="px-6 py-4 text-sm text-gray-900">{item.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.cantidad}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                    {item.category === 'Peligroso' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}">
                    {item.type}
                  </span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
