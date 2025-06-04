import { createRouter, createWebHistory } from 'vue-router'
import Home from '../components/Home.vue'
import Login from '../components/Login.vue'
import Register from '../components/Register.vue'
import DogSitterList from '../components/DogSitterList.vue'
import BookingList from '../components/BookingList.vue'
import UserProfile from '../components/UserProfile.vue'
import MyAnimals from '@/components/MyAnimals.vue'
import AnimalDetails from '@/components/AnimalDetails.vue'
import store from '../store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  },
  {
    path: '/my-animals',
    name: 'MyAnimals',
    component: MyAnimals,
    meta: { requiresAuth: true }
  },
  {
    path: '/my-animals/:id',
    name: 'AnimalDetails',
    component: AnimalDetails
  },
  {
    path: '/dogsitters',
    name: 'DogSitters',
    component: DogSitterList,
    meta: { requiresAuth: true }
  },
  {
    path: '/bookings',
    name: 'Bookings',
    component: BookingList,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: UserProfile,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router 