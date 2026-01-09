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
        category: (item.tipo_residuo === 'PELIGRO' || item.tipo_residuo === 'PELIGROSO') ? 'Peligroso' : 'No Peligroso',
        
        // AI Analysis Data
        analysisMaterial: item.analysis_material_name,
        analysisPhysicochemical: item.analysis_physicochemical ? JSON.parse(item.analysis_physicochemical) : null,
        analysisElemental: item.analysis_elemental ? JSON.parse(item.analysis_elemental) : null,
        analysisEngineering: item.analysis_engineering ? JSON.parse(item.analysis_engineering) : null,
        analysisValorization: item.analysis_valorization ? JSON.parse(item.analysis_valorization) : null,
        
        showDetails: false // UI State
      }));
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function toggleDetails(id: number) {
    const item = wasteItems.find(i => i.id === id);
    if (item) item.showDetails = !item.showDetails;
  }

  let searchQuery = $state('');

  let filteredItems = $derived(wasteItems.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    item.responsable.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.unidad.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (item.analysisMaterial && item.analysisMaterial.toLowerCase().includes(searchQuery.toLowerCase()))
  ));

</script>

<Navbar title="Registros Maestros de Residuos" />

<div class="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
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
        placeholder="Buscar por descripción, responsable, material IA..."
      />
    </div>
    <div class="flex gap-2">
      <a href="/intelligent-registry" class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Registro Inteligente (IA)
      </a>
      <a href="/waste-generation" class="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        Registro Simple
      </a>
    </div>
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
              <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            {#each filteredItems as item}
              <tr class="hover:bg-gray-50 transition-colors group">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-xs">{item.fecha}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.responsable}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.unidad}</td>
                <td class="px-6 py-4 text-sm text-gray-900">
                  {item.name}
                  {#if item.analysisMaterial}
                    <span class="block text-[10px] text-indigo-500 font-bold uppercase mt-1">
                      IA: {item.analysisMaterial}
                    </span>
                  {/if}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.cantidad}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                    {item.category === 'Peligroso' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}">
                    {item.type}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button 
                    on:click={() => toggleDetails(item.id)}
                    class="text-scientific-600 hover:text-scientific-900 flex items-center gap-1 ml-auto"
                  >
                    {item.showDetails ? 'Ocultar' : 'Ver Análisis IA'}
                    <svg class="w-4 h-4 transition-transform {item.showDetails ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </td>
              </tr>
              
              {#if item.showDetails}
                <tr class="bg-scientific-50/30">
                  <td colspan="7" class="px-6 py-6">
                    {#if item.analysisMaterial}
                      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in slide-in-from-top-2 duration-300">
                        <!-- Physicochemical -->
                        <div class="space-y-2">
                          <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Propiedades Físico-Químicas</h4>
                          <div class="bg-white border p-3 rounded-lg space-y-2">
                            {#each item.analysisPhysicochemical || [] as prop}
                              <div class="flex justify-between text-[11px] border-b border-gray-50 pb-1">
                                <span class="text-gray-500">{prop.name}</span>
                                <span class="font-bold text-gray-900">{prop.value}</span>
                              </div>
                            {/each}
                          </div>
                        </div>

                        <!-- Elemental -->
                        <div class="space-y-2">
                          <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Composición Elemental</h4>
                          <div class="flex flex-wrap gap-2">
                            {#each item.analysisElemental || [] as el}
                              <div class="bg-white border px-2 py-1 rounded text-[11px]">
                                <span class="text-gray-500">{el.label}:</span> <span class="font-bold text-indigo-600">{el.value}%</span>
                              </div>
                            {/each}
                          </div>
                        </div>

                        <!-- Engineering -->
                        <div class="space-y-2">
                          <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Evaluación de Ingeniería</h4>
                          <div class="bg-white border p-3 rounded-lg text-[11px] space-y-1">
                            <p><strong class="text-gray-900">Estructura:</strong> {item.analysisEngineering?.structure}</p>
                            <p><strong class="text-gray-900">Procesabilidad:</strong> {item.analysisEngineering?.processability}</p>
                          </div>
                        </div>

                        <!-- Valorization -->
                        <div class="space-y-2">
                          <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Rutas de Valorización</h4>
                          <div class="space-y-2">
                            {#each item.analysisValorization || [] as route}
                              <div class="bg-white border p-2 rounded-lg flex items-center justify-between gap-2 overflow-hidden">
                                <div class="min-w-0">
                                   <p class="text-[10px] font-bold text-scientific-700 truncate">{route.method}</p>
                                   <p class="text-[9px] text-gray-400 truncate">Output: {route.output}</p>
                                </div>
                                <span class="text-[10px] font-bold text-green-600">{route.score}%</span>
                              </div>
                            {/each}
                          </div>
                        </div>
                      </div>
                    {:else}
                      <div class="text-center py-4 text-sm text-gray-400 italic">
                        Este registro fue creado sin análisis de Selección Inteligente.
                      </div>
                    {/if}
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
