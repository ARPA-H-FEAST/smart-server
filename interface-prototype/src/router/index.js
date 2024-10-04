// Composables
import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue';
// import ModelView from '../views/ModelView.vue';

const routes = [
  {
    path: '/login',
    component: Login,
    // XXX - Looks the below code chunk is automatically handled by
    //       this version (4.0.0 as of Jan 2024) of the Vue Router
    //       when nginx passes the $uri argument
    // beforeEnter: (to, from, next) => {
    //   const { uri } = to.query;
    //   console.log("===> Found URI: %s", uri);
    //   if (uri != null && uri != '/predictmod') {
    //     next(false);
    //     router.push(uri);
    //   } else {
    //     next();
    //   }
    // }
  },
    {
        path: '/',
        component: Login,
    },
    {
        path: '/callback',
        component: () => import('../views/Callback.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('../views/NotFound.vue'),
    },
]

const router = createRouter({
  base: '/',
  history: createWebHistory(process.env.BASE_URL),
  // TODO: Might log useful information in the future(?)
  // watch: {
  //   '$route' (to, from) {
  //     console.log('Route changed from ' + from.path + ' to ' + to.path);
  //   },
  // },
  scrollBehavior(to, from, savedPosition) {
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
      }
    }
  },
  routes,
})

export default router
