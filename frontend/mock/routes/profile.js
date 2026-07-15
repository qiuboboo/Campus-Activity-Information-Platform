import { ACTIVITIES, USER_STATE } from '../db.js'
import { getCurrentUser, parseBody } from '../utils.js'

function userOrError(req) { const user = getCurrentUser(req); return user || { __status: 401, message: '请先登录' } }

export default [
  { method: 'GET', path: '/api/me/favorites', handler: async (req) => { const user=userOrError(req); if (user.__status) return user; const ids=USER_STATE.favorites[user.id] || []; const items=ACTIVITIES.filter(x=>ids.includes(x.id)); return { items,page:1,per_page:20,total:items.length } } },
  { method: 'GET', path: '/api/me/subscriptions', handler: async (req) => { const user=userOrError(req); if(user.__status)return user; return { items:USER_STATE.subscriptions[user.id] || [] } } },
  { method: 'POST', path: '/api/me/subscriptions', handler: async (req) => { const user=userOrError(req);if(user.__status)return user;const {keyword}=await parseBody(req);if(!keyword)return{__status:422,message:'请输入订阅关键词'};const items=USER_STATE.subscriptions[user.id] ||= [];const item={id:Date.now(),keyword:String(keyword),created_at:new Date().toISOString()};items.push(item);return item } },
  { method: 'DELETE', path: '/api/me/subscriptions/:id', handler: async(req)=>{const user=userOrError(req);if(user.__status)return user;USER_STATE.subscriptions[user.id]=(USER_STATE.subscriptions[user.id]||[]).filter(x=>x.id!==Number(req.params.id));return{success:true} } },
  { method: 'GET', path: '/api/me/notifications', handler: async(req)=>{const user=userOrError(req);if(user.__status)return user;return{items:USER_STATE.notifications[user.id]||[]} } },
  { method: 'POST', path: '/api/me/notifications/:id/read', handler: async(req)=>{const user=userOrError(req);if(user.__status)return user;const item=(USER_STATE.notifications[user.id]||[]).find(x=>x.id===Number(req.params.id));if(item)item.read=true;return{success:true} } },
  { method: 'POST', path: '/api/me/notifications/read-all', handler: async(req)=>{const user=userOrError(req);if(user.__status)return user;(USER_STATE.notifications[user.id]||[]).forEach(x=>x.read=true);return{success:true} } },
]
