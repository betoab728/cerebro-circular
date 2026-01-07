<script lang="ts">
  import { goto } from '$app/navigation';
  import { PUBLIC_API_URL } from '$env/static/public';
  
  let username = '';
  let password = '';
  let error = '';
  let isLoading = false;

  async function handleSubmit() {
    isLoading = true;
    error = '';
    
    try {
      const params = new URLSearchParams();
      params.append('username', username); // OAuth2 expects 'username'
      params.append('password', password);

      const response = await fetch(`${PUBLIC_API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: params
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      
      // Redirect to home or dashboard
      goto('/');
    } catch (e: any) {
      error = e.message;
      isLoading = false;
    }
  }
</script>

<div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
  <div class="sm:mx-auto sm:w-full sm:max-w-md">
    <img class="mx-auto h-32 w-auto mb-4" src="/logocerebro.png" alt="Logo">
    <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
      Iniciar Sesión
    <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
      Iniciar Sesión
    </h2>
  </div>

  <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
      <form class="space-y-6" on:submit|preventDefault={handleSubmit}>
        
        {#if error}
            <div class="rounded-md bg-red-50 p-4">
                <div class="flex">
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">Error</h3>
                        <div class="mt-2 text-sm text-red-700"><p>{error}</p></div>
                    </div>
                </div>
            </div>
        {/if}

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">
            Usuario
          </label>
          <div class="mt-1">
            <input id="username" name="username" type="text" autocomplete="username" required bind:value={username}
              class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-scientific-500 focus:border-scientific-500 sm:text-sm">
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <div class="mt-1">
            <input id="password" name="password" type="password" autocomplete="current-password" required bind:value={password}
              class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-scientific-500 focus:border-scientific-500 sm:text-sm">
          </div>
        </div>

        <div>
          <button type="submit" disabled={isLoading}
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-scientific-600 hover:bg-scientific-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-scientific-500 disabled:opacity-50">
            {#if isLoading}
                Cargando...
            {:else}
                Entrar
            {/if}
          </button>
        </div>
      </form>
      
    </div>
  </div>
</div>
