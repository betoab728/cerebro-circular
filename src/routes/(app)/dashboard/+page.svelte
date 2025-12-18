<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  
  // Mock data for KPIs
  const kpis = [
    { title: 'Residuos Procesados', value: '1,248 kg', change: '+12%', color: 'from-blue-500 to-blue-600' },
    { title: 'Tasa de Valorización', value: '86%', change: '+5%', color: 'from-green-500 to-green-600' },
    { title: 'Alertas de Toxicidad', value: '3', change: '-2', color: 'from-red-500 to-red-600', isNegative: true },
    { title: 'Registros Nuevos', value: '24', change: '+8', color: 'from-purple-500 to-purple-600' }
  ];
</script>

<Navbar title="Dashboard de Indicadores" />

<div class="p-6 md:p-8 space-y-8">
  <!-- KPIs Stats -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {#each kpis as kpi}
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">{kpi.title}</h3>
          <p class="text-2xl font-bold text-gray-900">{kpi.value}</p>
        </div>
        <div class="mt-4 flex items-center text-sm">
          {#if kpi.change.startsWith('+') && !kpi.isNegative}
            <span class="text-green-600 font-medium bg-green-50 px-2 py-0.5 rounded-full">{kpi.change}</span>
            <span class="text-gray-400 ml-2">vs mes anterior</span>
          {:else}
             <span class="text-red-500 font-medium bg-red-50 px-2 py-0.5 rounded-full">{kpi.change}</span>
             <span class="text-gray-400 ml-2">vs mes anterior</span>
          {/if}
        </div>
        <!-- Decorative line -->
        <div class="h-1 w-full mt-4 rounded-full bg-gradient-to-r {kpi.color} opacity-20">
          <div class="h-full rounded-full bg-gradient-to-r {kpi.color} w-3/4"></div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Charts Section -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">Composición de Residuos</h3>
      <div class="h-64 bg-gray-50 rounded-lg flex items-center justify-center border border-dashed border-gray-300">
        <span class="text-gray-400 text-sm">Gráfico de Pie (Orgánico vs Inorgánico)</span>
      </div>
    </div>
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">Tendencia de Ingreso Mensual</h3>
      <div class="h-64 bg-gray-50 rounded-lg flex items-center justify-center border border-dashed border-gray-300">
        <span class="text-gray-400 text-sm">Gráfico de Línea (Toneladas/Mes)</span>
      </div>
    </div>
  </div>

  <!-- Recent Activity -->
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-100">
      <h3 class="text-lg font-semibold text-gray-800">Actividad Reciente</h3>
    </div>
    <table class="w-full text-left text-sm text-gray-600">
      <thead class="bg-gray-50 text-gray-500 font-medium border-b border-gray-100">
        <tr>
          <th class="px-6 py-3">ID Lote</th>
          <th class="px-6 py-3">Tipo</th>
          <th class="px-6 py-3">Origen</th>
          <th class="px-6 py-3">Estado</th>
          <th class="px-6 py-3">Fecha</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr class="hover:bg-gray-50 transition-colors">
          <td class="px-6 py-4 font-medium text-gray-900">#RES-2024-001</td>
          <td class="px-6 py-4">Plástico PET</td>
          <td class="px-6 py-4">Sector Industrial A</td>
          <td class="px-6 py-4"><span class="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-medium">Procesado</span></td>
          <td class="px-6 py-4">15 Dic 2024</td>
        </tr>
        <tr class="hover:bg-gray-50 transition-colors">
          <td class="px-6 py-4 font-medium text-gray-900">#RES-2024-002</td>
          <td class="px-6 py-4">Residuos Orgánicos</td>
          <td class="px-6 py-4">Comedor Central</td>
          <td class="px-6 py-4"><span class="bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs font-medium">En Análisis</span></td>
          <td class="px-6 py-4">15 Dic 2024</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
