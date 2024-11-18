<template>

    <v-container>
      <v-row class="justify-center">
        <v-col>
            <v-card-title class="title text-center font-weight-bold">
              Login
            </v-card-title>
            <v-col>
              <v-row>
                <v-spacer></v-spacer>
                <v-text-field label="Email" v-model="email" style="width:50%"></v-text-field>
                <v-spacer></v-spacer>
              </v-row>
              <v-row>
                <v-spacer></v-spacer>
                <!-- <v-text-field label="Password" type="password" v-model="password" style="width:50%"></v-text-field> -->
                <v-text-field label="Password" type="text" v-model="password" style="width:50%"></v-text-field>
                <v-spacer></v-spacer>
              </v-row>
              <v-row :v-if="loginError">
              <p style="color:#FF0000">
                {{ loginError }}
              </p>
            </v-row>
            <!-- </form> -->
          </v-col>
          <v-col>
            <v-row class="justify-center">
              <v-btn 
                type="submit" 
                @click.prevent="login()" 
                :key="this.userStore.isAuthenticated">
                  {{ this.userStore.isAuthenticated ? `${this.userStore.user}` : "Login" }}
              </v-btn>
              <v-btn type="submit" @click.prevent="logout()">Logout</v-btn>
            </v-row>
          </v-col>
          <!-- </v-card> -->
        </v-col>
        <v-col>
          <!-- <v-card class=""> -->
          <v-card-title class="title text-center font-weight-bold">
              Register
          </v-card-title>
  
          <!-- <form @submit.prevent="login"> -->
          <!-- <form> -->
            <v-col>
              <v-row>
              <v-spacer></v-spacer>
              <v-text-field label="First Name" v-model="firstName" style="width:40%"></v-text-field>
              <v-spacer></v-spacer>
              <v-text-field label="Last Name" v-model="lastName"  style="width:40%"></v-text-field>
              <v-spacer></v-spacer>
              </v-row>
              <v-row>
                <v-spacer></v-spacer>
              <v-text-field label="Email Address" v-model="newEmail" style="width:40%"></v-text-field>
                <v-spacer></v-spacer>
              <v-text-field label="Confirm Email" v-model="newEmailConfirmation" style="width:40%"></v-text-field>
                <v-spacer></v-spacer>
              </v-row>
            </v-col>
            <v-col>
              <v-row>
                <v-spacer></v-spacer>
                <!-- <v-text-field label="Password" type="password" v-model="newPassword" style="width:40%"></v-text-field> -->
                <v-text-field label="Password" type="text" v-model="newPassword" style="width:40%"></v-text-field>
                <v-spacer></v-spacer>
                <!-- <v-text-field label="Confirm Password" type="password" v-model="newPasswordConfirmation" style="width:40%"></v-text-field> -->
                <v-text-field label="Confirm Password" type="text" v-model="newPasswordConfirmation" style="width:40%"></v-text-field>
                <v-spacer></v-spacer>
              <!-- <input type="text" v-model="email" /> -->
            </v-row>
            </v-col>
            <v-col>
              <v-row>
                <v-select 
                  :items="userRoles" 
                  v-model="roleSelection" 
                  :hint="'User role'"
                  item-title="title"
                  item-value="value"
                >
                </v-select>
              </v-row>
            </v-col>
            <v-row :v-if="userError" v-for="err in userError">
              <p style="color:#FF0000">
                {{ err }}
              </p>
            </v-row>
            <v-row class="justify-center">
              <v-btn type="submit" @click.prevent="createUser()">Create an Account</v-btn>
            </v-row>
        </v-col>
      </v-row>
    <v-container>
      <FHIRComplianceStatement />
      <OAuth />
    </v-container>

    </v-container>

    <v-container>
      <UserInfo />
    </v-container>
  
  </template>
  <script>
  import { onMounted, ref } from 'vue';
  
  import { useUserStore } from '@/stores/user';
  import OAuth from '@/components/OAuth.vue';
  import UserInfo from '@/components/UserInfo.vue';
  import FHIRComplianceStatement from '@/components/FHIRComplianceStatement.vue';

  export default {
  
    name: 'Login',
    setup() {
      const userStore = useUserStore();
      return { userStore };
    },
    data() {
        return {
          home: false,
          email: "",
          password: "",
          firstName: "",
          lastName: "",
          newEmail: "",
          newEmailConfirmation: "",
          newPassword: "",
          newPasswordConfirmation: "",
          loginError: "",
          roleSelection: 3,
          userRoles: [
            {title: "Patient", value: 1},
            {title: "Clinician", value:2},
            {title: "Researcher", value: 3},
            {title: "Administrator", value: 4},
            {title: "Automated backend", value: 5}],
          role: "",
          userError: [],
          loggedIn: false,
          showAdmin: false,
              }
      },
    mounted() {
      this.userStore.clearError();
      this.userStore.checkUser();
      if (this.userStore.isAdmin) {
        this.showAdmin = true;
      }
      if (this.userStore.user)  {
        this.loggedIn = true;
      }
      this.checkCode();
    },
    components: { FHIRComplianceStatement, OAuth, UserInfo },
    methods:
      {
        clearState() {
          this.email = "";
          this.password = "";
          this.newEmail = "";
          this.newEmailConfirmation = "",
          this.newPassword = "";
          this.newPasswordConfirmation = "",
          this.firstName = "";
          this.lastName = "",
          this.loginError = "";
          this.userError = [];
          this.userStore.clearError();
        },
        checkCode() {
          if (this.$route?.query?.code) {
            this.userStore.code = this.$route.query.code
          }
        },
        async login() {
          const success = await this.userStore.login(this.email, this.password);
          if (success) {
            // console.log("Login confirmed ---> (Success was %s)", success);
            this.clearState();
            if (this.userStore.isAdmin) {
              this.showAdmin = true;
            }
            if (this.userStore.user !== "") {
              this.loggedIn = true;
            }
          } else {
            // console.log("Error in login!");
            this.loginError = this.userStore.error;
            this.userStore.clearError();
          }
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
  
        async createUser() {
          this.userError = [];
          // console.log(
          //   "New Email: %s\nConfirmation: %s\nNPass: %s\nConfirm Pass: %s",
          //   this.newEmail,
          //   this.newEmailConfirmation,
          //   this.newPassword,
          //   this.newPasswordConfirmation
          // );
          // console.log("Bools: %s // %s", 
          // this.newEmail != this.newEmailConfirmation,
          // this.newPassword != this.newPasswordConfirmation
          // )
  
          if (this.newEmail != this.newEmailConfirmation) {
            this.userError.push("New email doesn't match\n");
          }
          if (this.newPassword != this.newPasswordConfirmation) {
            this.userError.push("New passwords don't match\n");
          }
          if (this.userError.length > 0) {
            return;
          }
          const success = await this.userStore.createUser(
            this.newEmail, this.newPassword, this.firstName, this.lastName, this.roleSelection
          );
          if (success) {
            this.clearState();
            if (this.userStore.isAdmin) {
              this.showAdmin = true;
            }
            if (this.userStore.user !== "") {
              this.loggedIn = true;
            }
            return;
          } else {
            // console.log("Error - Handling error on unsuccessful creation");
            this.userError.push(this.userStore.error);
            this.userStore.clearError();
          }
        },
  
      }
  }
  </script>
  