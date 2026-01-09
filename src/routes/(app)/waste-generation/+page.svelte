<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { fade } from 'svelte/transition';

  let formData = {
    responsable: '',
    unidad_generadora: '',
    tipo_residuo: '',
    caracteristica: '',
    cantidad: null,
    unidad_medida: '',
    volumen: null,
    peso_total: null,
    frecuencia: ''
  };

  let loading = false;
  let successMessage = '';
  let errorMessage = '';

  const unidadesGeneradoras = [
    'ADMINISTRACION', 'OPERACIONES', 'MANTENIMIENTO', 'MAESTRANZA', 
    'TOPICO', 'ALMACEN1', 'ALMACEN2', 'POLVORIN', 'COMEDOR', 'OTROS'
  ];

  const tiposResiduo = [
    'PELIGRO', 'NO PELIGROSO', 'NFU', 'RAEE', 'ESPECIAL', 'OTROS'
  ];

  const unidadesMedida = [
    'KILOGRAMO', 'METROS CUBICOS', 'OTROS'
  ];

  import { API_BASE_URL } from '$lib/config';

  async function handleSubmit() {
    loading = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await fetch(`${API_BASE_URL}/waste/generation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error al registrar los datos');
      }

      successMessage = 'Registro guardado exitosamente';
      formData = {
        responsable: '',
        unidad_generadora: '',
        tipo_residuo: '',
        caracteristica: '',
        cantidad: null,
        unidad_medida: '',
        volumen: null,
        peso_total: null,
        frecuencia: ''
      };
    } catch (error) {
      if (error.message.includes('Failed to fetch')) {
        errorMessage = 'No se pudo conectar con el servidor. ¿Está el backend encendido?';
      } else {
        errorMessage = error.message;
      }
    } finally {
      loading = false;
    }
  }
</script>

<Navbar title="Registro de Generación de Residuos" />

<div class="p-6 md:p-8 max-w-4xl mx-auto">
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
    <h2 class="text-xl font-bold text-gray-800 mb-6 border-b pb-4">Formulario de Registro</h2>

    {#if successMessage}
      <div transition:fade class="mb-6 p-4 bg-green-50 text-green-700 rounded-lg border border-green-200 flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        {successMessage}
      </div>
    {/if}

    {#if errorMessage}
      <div transition:fade class="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        {errorMessage}
      </div>
    {/if}

    <form on:submit|preventDefault={handleSubmit} class="space-y-6">
      
      <!-- Responsable -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Responsable</label>
        <input 
          type="text" 
          required
          bind:value={formData.responsable}
          class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
          placeholder="Nombre del responsable"
        />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Unidad Generadora -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad Generadora</label>
          <select 
            required
            bind:value={formData.unidad_generadora}
            class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
          >
            <option value="" disabled selected>Seleccione una opción</option>
            {#each unidadesGeneradoras as item}
              <option value={item}>{item}</option>
            {/each}
          </select>
        </div>

        <!-- Tipo de Residuo -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de Residuo</label>
          <select 
            required
            bind:value={formData.tipo_residuo}
            class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
          >
            <option value="" disabled selected>Seleccione una opción</option>
            {#each tiposResiduo as item}
              <option value={item}>{item}</option>
            {/each}
          </select>
        </div>
      </div>

      <!-- Característica -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Característica de los Residuos</label>
        <textarea 
          rows="3"
          required
          bind:value={formData.caracteristica}
          class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
          placeholder="Descripción física, estado, color, etc."
        ></textarea>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Cantidad -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Cantidad</label>
          <input 
            type="number" 
            step="0.01"
            required
            bind:value={formData.cantidad}
            class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
            placeholder="0.00"
          />
        </div>

        <!-- Unidad de Medida -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Medida</label>
          <select 
            required
            bind:value={formData.unidad_medida}
            class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
          >
            <option value="" disabled selected>Seleccione</option>
            {#each unidadesMedida as item}
              <option value={item}>{item}</option>
            {/each}
          </select>
        </div>

        <!-- Frecuencia -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Frecuencia</label>
          <input 
            type="text" 
            required
            bind:value={formData.frecuencia}
            class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm"
            placeholder="Ej: Diario, Semanal"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Volumen -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Volumen</label>
          <div class="relative rounded-md shadow-sm">
            <input 
              type="number" 
              step="0.01"
              required
              bind:value={formData.volumen}
              class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm pr-12"
              placeholder="0.00"
            />
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span class="text-gray-500 sm:text-sm">m³</span>
            </div>
          </div>
        </div>

        <!-- Peso Total -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Peso Total</label>
          <div class="relative rounded-md shadow-sm">
            <input 
              type="number" 
              step="0.01"
              required
              bind:value={formData.peso_total}
              class="w-full rounded-lg border-gray-300 focus:border-scientific-500 focus:ring-scientific-500 shadow-sm pr-12"
              placeholder="0.00"
            />
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span class="text-gray-500 sm:text-sm">kg</span>
            </div>
          </div>
        </div>
      </div>

      <div class="pt-4 flex justify-end">
        <button 
          type="submit" 
          disabled={loading}
          class="bg-scientific-600 hover:bg-scientific-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {#if loading}
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Guardando...
          {:else}
            Guardar Registro
          {/if}
        </button>
      </div>

    </form>
  </div>
</div>
