<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  
  export let isOpen = false;
  export let title = "Modal";
  export let onClose = () => {};
</script>

{#if isOpen}
  <div 
    class="fixed inset-0 z-50 overflow-y-auto" 
    aria-labelledby="modal-title" 
    role="dialog" 
    aria-modal="true"
  >
    <!-- Background backdrop -->
    <div 
      class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm transition-opacity"
      transition:fade={{ duration: 200 }}
      on:click={onClose} 
      role="presentation"
    ></div>

    <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <!-- Modal panel -->
      <div 
        class="relative transform overflow-hidden rounded-xl bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg border border-gray-100"
        transition:scale={{ duration: 200, start: 0.95 }}
      >
        <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
          <div class="sm:flex sm:items-start">
            <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
              <h3 class="text-lg font-semibold leading-6 text-gray-900 mb-4" id="modal-title">{title}</h3>
              <div class="mt-2">
                 <slot />
              </div>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
          <button 
            type="button" 
            class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
            on:click={onClose}
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
