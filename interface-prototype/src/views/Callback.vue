<template>

    <v-container>
      <v-row class="justify-center">
        <v-col>
            <v-card-title class="title text-center font-weight-bold">
              Welcome to the cool new OAuth App!
            </v-card-title>
            <v-row class="justify-center">
              <v-btn type="submit" @click.prevent="logout()">Logout</v-btn>
                <FHIRComplianceStatement />
                <FHIRQueryAPI />
              <o-auth />
            </v-row>
        </v-col>
      </v-row>
  </v-container>

  <UserInfo />
  
  </template>
  <script>
  import { onMounted, ref } from 'vue';
  
  import { useUserStore } from '@/stores/user';
  import OAuth from '@/components/OAuth.vue';
  import UserInfo from '@/components/UserInfo.vue';
  import FHIRComplianceStatement from '@/components/FHIRComplianceStatement.vue';
  import FHIRQueryAPI from '@/components/FHIRQueryAPI.vue';

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
      this.checkCode();
    },
    components: { FHIRComplianceStatement, FHIRQueryAPI, OAuth, UserInfo },
    methods:
      {
        clearState() {
          this.userStore.clearError();
        },
        checkCode() {
          if (this.$route.query?.code) {
            this.userStore.code = this.$route.query.code
          }
        },
        async logout() {
          const success = await this.userStore.logout();
          if (success) {
            this.userStore.clearError();
            this.showAdmin = false;
            this.loggedIn = false;
            this.$router.push("/login")
          } else {
            // Error handling logic
            // console.log("Error on logout!")
          }
        },  
      },
    }
  </script>
  