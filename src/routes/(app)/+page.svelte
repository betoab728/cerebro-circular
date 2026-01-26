<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  onMount(() => {
    goto('/dashboard');
  });
</script>

<div class="h-full flex items-center justify-center p-1">
  <p class="text-gray-500">Redirigiendo a CEREBRO CIRCULAR.....</p>
</div>
