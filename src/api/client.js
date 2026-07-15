import axios from 'axios'

const client = axios.create({
  baseURL: 'https://ai-project-8ww1.onrender.com/api',
  timeout: 15000,
})

export default client