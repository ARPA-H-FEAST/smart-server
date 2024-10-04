<template>

    <v-container>
      <v-row class="justify-center">
        <v-col>
            <v-card-title class="title text-center font-weight-bold">
              Welcome to the cool new OAuth App!
            </v-card-title>
            <v-col>
            <v-row class="justify-center">
              <v-btn type="submit" @click.prevent="logout()">Logout</v-btn>
            </v-row>
          </v-col>
        </v-col>
      </v-row>
  </v-container>

  <v-container>
        <v-card>
            <v-card-title class="text-center">
                Current User Information
            </v-card-title>
            <v-col>
                User: {{ userStore.user }}<br>
                Password: {{ userStore.password }}<br>
                Authenticated: {{ userStore.isAuthenticated }}<br>
                Token: {{ userStore.token }}<br>
            </v-col>
        </v-card>
    </v-container>
  
  </template>
  <script>
  import { onMounted, ref } from 'vue';
  
  import { useUserStore } from '@/stores/user';
  
  export default {
  
    name: 'Callback',
    setup() {
      const userStore = useUserStore();
      return { userStore };
    },
    data() {
        return {}
      },
    mounted() {
      this.userStore.clearError();
      this.userStore.checkUser();
    },
    components: {  },
    methods:
      {
        clearState() {
          this.userStore.clearError();
        },
        async logout() {
          const success = await this.userStore.logout();
          if (success) {
            this.userStore.clearError();
            this.showAdmin = false;
            this.loggedIn = false;
          } else {
            // Error handling logic
            // console.log("Error on logout!")
          }
        },  
      },
    }
  </script>
  