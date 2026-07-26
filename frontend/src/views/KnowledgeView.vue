<template>
  <div class="knowledge-container">
    <h1>糖尿病知识库</h1>
    
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="category-card">
          <template #header>
            <div class="card-header">
              <span>知识分类</span>
            </div>
          </template>
          
          <el-menu
            :default-active="activeCategory"
            class="category-menu"
            @select="handleCategorySelect"
          >
            <el-menu-item index="all">
              <el-icon><Document /></el-icon>
              <span>全部知识</span>
            </el-menu-item>
            <el-menu-item index="basic">
              <el-icon><InfoFilled /></el-icon>
              <span>基础知识</span>
            </el-menu-item>
            <el-menu-item index="diet">
              <el-icon><KnifeFork /></el-icon>
              <span>饮食管理</span>
            </el-menu-item>
            <el-menu-item index="medication">
              <el-icon><FirstAidKit /></el-icon>
              <span>药物治疗</span>
            </el-menu-item>
            <el-menu-item index="exercise">
              <el-icon><Trophy /></el-icon>
              <span>运动指导</span>
            </el-menu-item>
            <el-menu-item index="complication">
              <el-icon><Warning /></el-icon>
              <span>并发症预防</span>
            </el-menu-item>
            <el-menu-item index="psychology">
              <el-icon><Service /></el-icon>
              <span>心理健康</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <el-card class="search-card">
          <el-input
            v-model="searchQuery"
            placeholder="搜索知识库内容"
            prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-card>
        
        <el-card v-if="isAdmin" class="action-card">
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>添加知识
          </el-button>
        </el-card>
        
        <div v-loading="loading" class="knowledge-list">
          <el-empty v-if="knowledgeList.length === 0" description="暂无相关知识内容" />
          
          <el-card v-for="item in knowledgeList" :key="item.id" class="knowledge-item">
            <template #header>
              <div class="knowledge-header">
                <h3>{{ item.title }}</h3>
                <div class="knowledge-tags">
                  <el-tag size="small">{{ getCategoryName(item.category) }}</el-tag>
                </div>
              </div>
            </template>
            
            <div class="knowledge-content">
              <div v-html="item.summary" class="knowledge-summary"></div>
              <div class="knowledge-actions">
                <el-button text @click="showDetail(item)">
                  阅读全文
                </el-button>
                <div v-if="isAdmin" class="admin-actions">
                  <el-button text type="primary" @click="editKnowledge(item)">
                    <el-icon><Edit /></el-icon>编辑
                  </el-button>
                  <el-button text type="danger" @click="deleteKnowledge(item)">
                    <el-icon><Delete /></el-icon>删除
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
          
          <div class="pagination-container">
            <el-pagination
              background
              layout="prev, pager, next"
              :total="totalItems"
              :page-size="pageSize"
              :current-page="currentPage"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 知识详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentKnowledge.title"
      width="70%"
      destroy-on-close
    >
      <div class="knowledge-detail">
        <div class="knowledge-meta">
          <el-tag size="small">{{ getCategoryName(currentKnowledge.category) }}</el-tag>
          <span class="knowledge-date">发布时间: {{ formatDate(currentKnowledge.createdAt) }}</span>
        </div>
        
        <div v-html="currentKnowledge.content" class="knowledge-full-content"></div>
      </div>
    </el-dialog>
    
    <!-- 添加/编辑知识对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="isEditing ? '编辑知识' : '添加知识'"
      width="70%"
      destroy-on-close
    >
      <el-form :model="knowledgeForm" :rules="rules" ref="knowledgeFormRef" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="knowledgeForm.title" placeholder="请输入知识标题" />
        </el-form-item>
        
        <el-form-item label="分类" prop="category">
          <el-select v-model="knowledgeForm.category" placeholder="请选择分类">
            <el-option label="基础知识" value="basic" />
            <el-option label="饮食管理" value="diet" />
            <el-option label="药物治疗" value="medication" />
            <el-option label="运动指导" value="exercise" />
            <el-option label="并发症预防" value="complication" />
            <el-option label="心理健康" value="psychology" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="摘要" prop="summary">
          <el-input v-model="knowledgeForm.summary" type="textarea" :rows="3" placeholder="请输入知识摘要" />
        </el-form-item>
        
        <el-form-item label="内容" prop="content">
          <div class="editor-container">
            <!-- 这里可以集成富文本编辑器，如 TinyMCE, CKEditor 等 -->
            <el-input v-model="knowledgeForm.content" type="textarea" :rows="10" placeholder="请输入知识内容" />
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveKnowledge" :loading="saveLoading">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, InfoFilled, KnifeFork, FirstAidKit, Trophy, Warning, Service, Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { format } from 'date-fns'

// 用户权限
const isAdmin = ref(true) // 实际应用中应该从用户权限中获取

// 分类相关
const activeCategory = ref('all')
const getCategoryName = (category) => {
  const categoryMap = {
    basic: '基础知识',
    diet: '饮食管理',
    medication: '药物治疗',
    exercise: '运动指导',
    complication: '并发症预防',
    psychology: '心理健康'
  }
  return categoryMap[category] || category
}

// 搜索相关
const searchQuery = ref('')
const handleSearch = () => {
  currentPage.value = 1
  fetchKnowledgeList()
}

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const totalItems = ref(0)

// 加载状态
const loading = ref(false)
const saveLoading = ref(false)

// 知识列表数据
const knowledgeList = ref([])

// 获取知识列表
const fetchKnowledgeList = async () => {
  try {
    loading.value = true
    
    // 这里应该调用后端API获取数据
    // const response = await api.getKnowledgeList({
    //   page: currentPage.value,
    //   pageSize: pageSize.value,
    //   category: activeCategory.value !== 'all' ? activeCategory.value : null,
    //   query: searchQuery.value
    // })
    
    // 模拟数据
    setTimeout(() => {
      knowledgeList.value = [
        {
          id: 1,
          title: '糖尿病的基本知识',
          category: 'basic',
          summary: '糖尿病是一种由于胰岛素分泌不足或其生物作用受损，或两者兼有引起的以血糖升高为特征的代谢性疾病。',
          content: '<p>糖尿病是一种由于胰岛素分泌不足或其生物作用受损，或两者兼有引起的以血糖升高为特征的代谢性疾病。</p><p>长期高血糖会导致各种组织，特别是眼、肾、心脏、血管和神经的慢性损害和功能障碍。</p><p>糖尿病主要分为1型糖尿病、2型糖尿病、特殊类型糖尿病和妊娠糖尿病。</p>',
          createdAt: '2023-05-15T08:30:00Z',
          updatedAt: '2023-05-15T08:30:00Z'
        },
        {
          id: 2,
          title: '糖尿病患者的饮食原则',
          category: 'diet',
          summary: '糖尿病患者的饮食管理是治疗的基础，合理的饮食计划可以帮助控制血糖、血脂和体重。',
          content: '<p>糖尿病患者的饮食管理是治疗的基础，合理的饮食计划可以帮助控制血糖、血脂和体重。</p><p>饮食原则包括：控制总热量摄入、均衡营养素比例、规律进餐时间、选择低升糖指数食物、限制单糖和精制碳水化合物摄入。</p>',
          createdAt: '2023-05-20T10:15:00Z',
          updatedAt: '2023-05-20T10:15:00Z'
        }
      ]
      totalItems.value = 2
      loading.value = false
    }, 500)
    
  } catch (error) {
    console.error('获取知识列表失败:', error)
    ElMessage.error('获取知识列表失败')
    loading.value = false
  }
}

// 处理分类选择
const handleCategorySelect = (index) => {
  activeCategory.value = index
  currentPage.value = 1
  fetchKnowledgeList()
}

// 处理分页变化
const handlePageChange = (page) => {
  currentPage.value = page
  fetchKnowledgeList()
}

// 知识详情相关
const detailDialogVisible = ref(false)
const currentKnowledge = ref({})

const showDetail = (item) => {
  currentKnowledge.value = item
  detailDialogVisible.value = true
}

// 添加/编辑知识相关
const editDialogVisible = ref(false)
const isEditing = ref(false)
const knowledgeFormRef = ref(null)

const knowledgeForm = reactive({
  id: null,
  title: '',
  category: '',
  summary: '',
  content: ''
})

const rules = {
  title: [
    { required: true, message: '请输入知识标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择知识分类', trigger: 'change' }
  ],
  summary: [
    { required: true, message: '请输入知识摘要', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入知识内容', trigger: 'blur' }
  ]
}

// 显示添加对话框
const showAddDialog = () => {
  isEditing.value = false
  Object.keys(knowledgeForm).forEach(key => {
    knowledgeForm[key] = key === 'id' ? null : ''
  })
  editDialogVisible.value = true
}

// 编辑知识
const editKnowledge = (item) => {
  isEditing.value = true
  Object.keys(knowledgeForm).forEach(key => {
    knowledgeForm[key] = item[key]
  })
  editDialogVisible.value = true
}

// 保存知识
const saveKnowledge = async () => {
  if (!knowledgeFormRef.value) return
  
  await knowledgeFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        saveLoading.value = true
        
        // 这里应该调用后端API保存数据
        // if (isEditing.value) {
        //   await api.updateKnowledge(knowledgeForm.id, knowledgeForm)
        // } else {
        //   await api.createKnowledge(knowledgeForm)
        // }
        
        // 模拟保存成功
        setTimeout(() => {
          ElMessage.success(isEditing.value ? '知识更新成功' : '知识添加成功')
          editDialogVisible.value = false
          fetchKnowledgeList()
          saveLoading.value = false
        }, 500)
        
      } catch (error) {
        console.error('保存知识失败:', error)
        ElMessage.error('保存知识失败')
        saveLoading.value = false
      }
    }
  })
}

// 删除知识
const deleteKnowledge = (item) => {
  ElMessageBox.confirm('确定要删除这条知识吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 这里应该调用后端API删除数据
      // await api.deleteKnowledge(item.id)
      
      // 模拟删除成功
      setTimeout(() => {
        ElMessage.success('知识删除成功')
        fetchKnowledgeList()
      }, 500)
      
    } catch (error) {
      console.error('删除知识失败:', error)
      ElMessage.error('删除知识失败')
    }
  }).catch(() => {})
}

// 格式化日期
const formatDate = (dateString) => {
  try {
    return format(new Date(dateString), 'yyyy-MM-dd HH:mm')
  } catch (error) {
    return dateString
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchKnowledgeList()
})
</script>

<style scoped>
.knowledge-container {
  padding: 20px;
}

.category-card, .search-card, .action-card {
  margin-bottom: 20px;
}

.category-menu {
  border-right: none;
}

.knowledge-list {
  min-height: 400px;
}

.knowledge-item {
  margin-bottom: 20px;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-header h3 {
  margin: 0;
}

.knowledge-summary {
  margin-bottom: 15px;
  line-height: 1.6;
}

.knowledge-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-actions {
  display: flex;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.knowledge-detail .knowledge-meta {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.knowledge-date {
  color: #909399;
  font-size: 14px;
}

.knowledge-full-content {
  line-height: 1.8;
}

.editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>
