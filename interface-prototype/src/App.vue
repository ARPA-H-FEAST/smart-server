<template>
<!-- <nav>
  <RouterLink to="/login">Go to login</RouterLink>
  <RouterLink to="/callback">Go to callback</RouterLink>
</nav> -->
<v-app>
      <div class="text-center">
      <h2>Welcome to the MGPC on FHIR Login Testing Interface</h2>
      </div>
    <v-main>
      <p>
        <strong>Current router path:</strong> {{ $route.fullPath }}
      </p>
      <RouterView></RouterView>
      <!-- <FileUpload upload-target-u-r-l="test" /> -->
      <!-- <Login /> -->

    </v-main>
  </v-app>
</template>

<script setup>
  import FileUpload from './components/FileUpload.vue';
  import Login from './views/Login.vue';

</script>

<style>
  #app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: left;
    color: #509fee;
    margin-top: 60px;
  }
</style>
