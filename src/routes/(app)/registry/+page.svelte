<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';

  let wasteItems = [
    { id: 1, code: 'R-ORG-01', name: 'Cáscara de Café', category: 'Orgánico', hazard: 'No Peligroso', potential: 'Bioenergía' },
    { id: 2, code: 'R-INO-05', name: 'Virutas de Aluminio', category: 'Inorgánico', hazard: 'Inflamable', potential: 'Reciclaje' },
    { id: 3, code: 'R-ORG-03', name: 'Bagazo de Caña', category: 'Orgánico', hazard: 'No Peligroso', potential: 'Biopelículas' },
  ];

  let searchQuery = $state('');

  // Svelte 5 derived state
  // If Svelte 4, use $: filteredItems = ...
  // Assuming Svelte 5 since 'sv' was used.
  // Actually, let's use a function or simpler approach to be safe if version is ambiguous, 
  // but let's try standard reactivity.
  
  let filteredItems = $derived(wasteItems.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    item.code.toLowerCase().includes(searchQuery.toLowerCase())
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
        placeholder="Buscar por código o nombre..."
      />
    </div>
    <a href="/waste-generation" class="bg-scientific-600 hover:bg-scientific-700 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
      Nuevo Residuo
    </a>
  </div>

  <!-- Data Grid -->
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código Interno</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre del Residuo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peligrosidad</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Potencial de Valorización</th>
            <th scope="col" class="relative px-6 py-3">
              <span class="sr-only">Editar</span>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each filteredItems as item}
            <tr class="hover:bg-gray-50 transition-colors group">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-scientific-600">{item.code}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">{item.name}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                  {item.category === 'Orgánico' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                  {item.category}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {#if item.hazard === 'No Peligroso'}
                   <span class="text-green-600 flex items-center gap-1">
                     <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                     No Peligroso
                   </span>
                {:else}
                   <span class="text-red-600 flex items-center gap-1">
                     <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                     {item.hazard}
                   </span>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.potential}</td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button class="text-scientific-600 hover:text-scientific-900 group-hover:opacity-100 opacity-0 transition-opacity">Editar</button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
