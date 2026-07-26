<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="16" :lg="18">
        <el-row :gutter="20">
          <!-- 欢迎卡片 -->
          <el-col :span="24">
            <el-card class="welcome-card">
              <div v-if="loading" class="welcome-loader-container">
                <div class="e-card playing">
                  <div class="image"></div>

                  <div class="wave"></div>
                  <div class="wave"></div>
                  <div class="wave"></div>


                  <div class="infotop">

                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="icon">
                      <path fill="currentColor" d="M19.4133 4.89862L14.5863 2.17544C12.9911 1.27485 11.0089 1.27485 9.41368 2.17544L4.58674
    4.89862C2.99153 5.7992 2 7.47596 2 9.2763V14.7235C2 16.5238 2.99153 18.2014 4.58674 19.1012L9.41368
    21.8252C10.2079 22.2734 11.105 22.5 12.0046 22.5C12.6952 22.5 13.3874 22.3657 14.0349 22.0954C14.2204
    22.018 14.4059 21.9273 14.5872 21.8252L19.4141 19.1012C19.9765 18.7831 20.4655 18.3728 20.8651
    17.8825C21.597 16.9894 22 15.8671 22 14.7243V9.27713C22 7.47678 21.0085 5.7992 19.4133 4.89862ZM4.10784
    14.7235V9.2763C4.10784 8.20928 4.6955 7.21559 5.64066 6.68166L10.4676 3.95848C10.9398 3.69152 11.4701
    3.55804 11.9996 3.55804C12.5291 3.55804 13.0594 3.69152 13.5324 3.95848L18.3593 6.68166C19.3045 7.21476
    19.8922 8.20928 19.8922 9.2763V9.75997C19.1426 9.60836 18.377 9.53091 17.6022 9.53091C14.7929 9.53091
    12.1041 10.5501 10.0309 12.3999C8.36735 13.8847 7.21142 15.8012 6.68783 17.9081L5.63981 17.3165C4.69466
    16.7834 4.10699 15.7897 4.10699 14.7235H4.10784ZM10.4676 20.0413L8.60933 18.9924C8.94996 17.0479 9.94402
    15.2665 11.4515 13.921C13.1353 12.4181 15.3198 11.5908 17.6022 11.5908C18.3804 11.5908 19.1477 11.6864
    19.8922 11.8742V14.7235C19.8922 15.2278 19.7589 15.7254 19.5119 16.1662C18.7615 15.3596 17.6806 14.8528
     16.4783 14.8528C14.2136 14.8528 12.3781 16.6466 12.3781 18.8598C12.3781 19.3937 12.4861 19.9021 12.68
     20.3676C11.9347 20.5316 11.1396 20.4203 10.4684 20.0413H10.4676Z"></path></svg><br>      
                    UI / EX Designer
                    <br>
                    <div class="name">MikeAndrewDesigner</div>
                  </div>
                </div>
              </div>
              <div v-else class="welcome-content">
                <div class="welcome-text">
                  <h2>您好，{{ userName }}！</h2>
                  <p>欢迎使用糖尿病智能健康助理，今天是 {{ currentDate }}</p>
                </div>
                <div class="welcome-actions">
                  <button class="button" @click="goToGlucoseRecord">
                    <div class="bg"></div>
                    <div class="wrap">
                      <div class="content">
                        <div class="char state-1">
                          <span data-label="录" style="--i: 0">录</span>
                          <span data-label="记" style="--i: 1">记</span>
                          <span data-label="血" style="--i: 2">血</span>
                          <span data-label="糖" style="--i: 3">糖</span>
                        </div>
                      </div>
                    </div>
                  </button>
                  <button class="button" @click="goToAssistant">
                    <div class="bg"></div>
                    <div class="wrap">
                      <div class="content">
                        <div class="char state-1">
                          <span data-label="询" style="--i: 0">询</span>
                          <span data-label="咨" style="--i: 1">咨</span>
                          <span data-label="助" style="--i: 2">助</span>
                          <span data-label="理" style="--i: 3">理</span>
                        </div>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- 血糖趋势图 -->
          <el-col :span="24">
            <el-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>血糖趋势</span>
                  <div class="header-actions">
                    <el-button type="primary" size="small" circle @click="refreshData">
                      <el-icon><Refresh /></el-icon>
                    </el-button>
                    <el-radio-group v-model="glucosePeriod" size="small">
                      <el-radio-button label="week">周</el-radio-button>
                      <el-radio-button label="month">月</el-radio-button>
                    </el-radio-group>
                  </div>
                </div>
              </template>
              <div v-if="loading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              <div v-else-if="!hasGlucoseData" class="empty-data">
                <el-empty description="暂无血糖数据">
                  <el-button type="primary" @click="goToGlucoseRecord">记录血糖</el-button>
                </el-empty>
              </div>
              <div v-else class="chart-container">
                <div ref="glucoseChartRef" class="chart" :key="chartKey"></div>
              </div>
            </el-card>
          </el-col>
          
          <!-- 三卡片布局：健康指标、饮食建议、今日饮食 -->
          <el-col :xs="24" :sm="8">
            <el-card class="metric-card">
              <template #header>
                <div class="card-header">
                  <span>健康指标</span>
                </div>
              </template>
              <div class="metrics-container">
                <div class="metric-item">
                  <div class="metric-label">体重</div>
                  <div class="metric-value">{{ healthMetrics.weight || '--' }} kg</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">血压</div>
                  <div class="metric-value">{{ healthMetrics.bloodPressure || '--' }}</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">BMI</div>
                  <div class="metric-value">{{ healthMetrics.bmi || '--' }}</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">今日步数</div>
                  <div class="metric-value">{{ healthMetrics.steps || '--' }}</div>
                </div>
              </div>
              <div class="card-footer">
                <el-button text @click="goToHealthData">查看更多</el-button>
              </div>
            </el-card>
          </el-col>
          
          <!-- 血糖饮食建议卡片 - 从右侧移动到左侧 -->
          <el-col :xs="24" :sm="8">
            <el-card class="diet-suggestion-card">
              <template #header>
                <div class="card-header">
                  <span>血糖饮食建议</span>
                  <el-button type="text" @click="refreshDietSuggestions">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </div>
              </template>
              <div v-if="loadingDietSuggestions" class="loading-container">
                <el-skeleton :rows="3" animated />
              </div>
              <div v-else-if="!hasDietSuggestions" class="empty-data">
                <el-empty description="暂无饮食建议" :image-size="60">
                  <template #description>
                    <p>需要血糖数据才能生成饮食建议</p>
                  </template>
                  <el-button size="small" @click="fetchDietSuggestions">获取建议</el-button>
                </el-empty>
              </div>
              <div v-else>
                <div class="diet-status-banner" :class="getDietStatusClass(dietSuggestions.glucose_status)">
                  <el-icon><InfoFilled /></el-icon>
                  <span>{{ dietSuggestions.current_status }}</span>
                </div>
                
                <div class="diet-suggestion-content">
                  <p class="suggestion-text">{{ dietSuggestions.quick_suggestion }}</p>
                  
                  <div class="food-section">
                    <h4>推荐食物</h4>
                    <div class="food-tags">
                      <el-tag 
                        v-for="(food, index) in dietSuggestions.recommended_foods" 
                        :key="index"
                        type="success"
                        effect="light"
                        class="food-tag"
                      >
                        {{ food }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <div class="food-section">
                    <h4>建议避免</h4>
                    <div class="food-tags">
                      <el-tag 
                        v-for="(food, index) in dietSuggestions.foods_to_avoid" 
                        :key="index"
                        type="danger"
                        effect="light"
                        class="food-tag"
                      >
                        {{ food }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <el-divider content-position="center">下一餐建议</el-divider>
                  
                  <div class="next-meal">
                    <div class="meal-type-selector">
                      <el-radio-group v-model="selectedMealType" size="small" @change="updateMealSuggestion">
                        <el-radio-button label="breakfast">早餐</el-radio-button>
                        <el-radio-button label="lunch">午餐</el-radio-button>
                        <el-radio-button label="dinner">晚餐</el-radio-button>
                        <el-radio-button label="snack">加餐</el-radio-button>
                      </el-radio-group>
                    </div>
                    <div class="meal-suggestion">
                      {{ dietSuggestions.meal_plan_example || '暂无特定餐食建议' }}
                    </div>
                  </div>
                  
                  <div class="card-footer">
                    <el-button type="primary" size="small" @click="showDetailedDietSuggestions">
                      获取详细建议
                    </el-button>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- 饮食记录卡片 -->
          <el-col :xs="24" :sm="8">
            <el-card class="diet-card">
              <template #header>
                <div class="card-header">
                  <span>今日饮食</span>
                </div>
              </template>
              <div v-if="loadingDietSuggestions" class="diet-loader-container">
                <div class="main">
                  <svg
                    width="168"
                    height="158"
                    viewBox="0 0 168 158"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <g id="pizza">
                      <rect width="168" height="158" fill="none"></rect>
                      <g id="slice6">
                        <g id="slice">
                          <mask id="path-1-inside-1_7_2" fill="white">
                            <path
                              d="M110 34.8997C118.513 39.4198 125.582 45.921 130.497 53.75C135.412 61.579 138 70.4598 138 79.5L82 79.5L110 34.8997Z"
                            ></path>
                          </mask>
                          <path
                            d="M110 34.8997C118.513 39.4198 125.582 45.921 130.497 53.75C135.412 61.579 138 70.4598 138 79.5L82 79.5L110 34.8997Z"
                            fill="#FDDBA9"
                            stroke="#EE9758"
                            stroke-width="2"
                            mask="url(#path-1-inside-1_7_2)"
                          ></path>
                        </g>
                        <g id="pepperoni">
                          <circle cx="114" cy="63" r="6" fill="#F12424"></circle>
                          <circle cx="114" cy="63" r="6" fill="#F12424"></circle>
                        </g>
                        <g id="mushroom">
                          <path
                            d="M96.3127 75.3748C93.8388 74.3499 93.5395 72.1249 96.4349 66.9246C100.861 64.107 105.48 66.5248 103.603 67.4062C101.726 68.2876 101.517 69.215 101.78 69.3984C101.78 69.3984 105.126 71.2856 104.991 72.8193C104.856 74.353 103.753 74.1725 103.409 74.5483C103.066 74.9242 99.9579 71.3905 99.9579 71.3905C96.0194 74.1256 98.7867 76.3997 96.3127 75.3748Z"
                            fill="#E3DDDD"
                          ></path>
                          <path
                            d="M99.9579 71.3905C96.0194 74.1256 98.7867 76.3997 96.3127 75.3748C93.8388 74.3499 93.5395 72.1249 96.4349 66.9246C100.861 64.107 105.48 66.5248 103.603 67.4062C101.726 68.2876 101.517 69.215 101.78 69.3984M99.9579 71.3905C99.9579 71.3905 103.066 74.9242 103.409 74.5483C103.753 74.1725 104.856 74.353 104.991 72.8193C105.126 71.2856 101.78 69.3984 101.78 69.3984M99.9579 71.3905L101.78 69.3984"
                            stroke="black"
                          ></path>
                        </g>
                        <path
                          id="onion"
                          d="M129.841 65.2587C127.54 64.2211 127.021 63.5697 127.016 62.3249C127.666 61.9214 128.094 61.8629 129.071 62.3249C130.14 62.8474 130.783 63.5952 131.961 65.2587C131.313 66.9451 130.895 67.8704 129.392 69.2403C131.161 70.4193 131.537 72.3751 131.961 72.3837C132.384 72.3923 129.231 76.9243 129.071 77.9719C127.662 78.0881 127.229 77.8597 127.016 76.994C126.863 74.9998 127.829 74.044 129.841 72.3837C128.109 71.4403 127.329 70.8249 127.016 69.2403C126.968 67.7728 127.329 66.9206 129.841 65.2587Z"
                          fill="#FFFBFB"
                          stroke="black"
                        ></path>
                        <path
                          id="pepper"
                          d="M121.34 55.4341C123.716 54.3509 124.645 54.4077 125.824 55.2995C125.811 56.107 125.607 56.4894 124.578 56.9337C123.436 57.4079 122.34 57.3806 120.055 57.1194C118.855 55.39 118.235 54.3915 117.853 52.2096C115.667 52.7671 113.592 51.6583 113.327 51.9889C113.062 52.3195 110.695 46.5489 109.803 45.6669C110.547 44.4628 111.025 44.2833 111.972 44.7368C113.948 46.0515 114.265 47.5081 114.612 50.3036C116.554 49.6053 117.608 49.4283 119.294 50.32C120.708 51.3389 121.295 52.2392 121.34 55.4341Z"
                          fill="#1EAA07"
                          stroke="#FDDBA9"
                        ></path>
                      </g>
                      <g id="slice5">
                        <g id="slice_2">
                          <mask id="path-7-inside-2_7_2" fill="white">
                            <path
                              d="M54 34.8997C62.5131 30.3796 72.1699 28 82 28C91.8301 28 101.487 30.3796 110 34.8997L82 79.5L54 34.8997Z"
                            ></path>
                          </mask>
                          <path
                            d="M54 34.8997C62.5131 30.3796 72.1699 28 82 28C91.8301 28 101.487 30.3796 110 34.8997L82 79.5L54 34.8997Z"
                            fill="#FDDBA9"
                            stroke="#EE9758"
                            stroke-width="2"
                            mask="url(#path-7-inside-2_7_2)"
                          ></path>
                        </g>
                        <g id="pepperoni_2">
                          <circle cx="82" cy="56" r="6" fill="#F12424"></circle>
                          <circle cx="82" cy="56" r="6" fill="#F12424"></circle>
                        </g>
                        <g id="mushroom_2">
                          <path
                            d="M91.3127 43.3748C88.8388 42.3499 88.5395 40.1249 91.4349 34.9246C95.8614 32.107 100.48 34.5248 98.603 35.4062C96.7261 36.2876 96.5167 37.215 96.7805 37.3984C96.7805 37.3984 100.126 39.2856 99.9914 40.8193C99.8563 42.353 98.7534 42.1725 98.4095 42.5483C98.0656 42.9242 94.9579 39.3905 94.9579 39.3905C91.0194 42.1256 93.7867 44.3997 91.3127 43.3748Z"
                            fill="#E3DDDD"
                          ></path>
                          <path
                            d="M94.9579 39.3905C91.0194 42.1256 93.7867 44.3997 91.3127 43.3748C88.8388 42.3499 88.5395 40.1249 91.4349 34.9246C95.8614 32.107 100.48 34.5248 98.603 35.4062C96.7261 36.2876 96.5167 37.215 96.7805 37.3984M94.9579 39.3905C94.9579 39.3905 98.0656 42.9242 98.4095 42.5483C98.7534 42.1725 99.8563 42.353 99.9914 40.8193C100.126 39.2856 96.7805 37.3984 96.7805 37.3984M94.9579 39.3905L96.7805 37.3984"
                            stroke="black"
                          ></path>
                        </g>
                        <path
                          id="pepper_2"
                          d="M92.1727 48.6661C93.9594 46.7623 94.8409 46.462 96.27 46.8398C96.5642 47.5919 96.5204 48.0231 95.7373 48.8247C94.8608 49.6968 93.8366 50.0874 91.6233 50.713C89.857 49.5684 88.9042 48.8801 87.7226 47.0063C85.9121 48.3518 83.5712 48.1136 83.4516 48.52C83.3319 48.9264 78.9513 44.4862 77.7915 44.0087C78.0235 42.6121 78.3975 42.2646 79.4458 42.3247C81.7725 42.7912 82.6182 44.0187 84.0009 46.473C85.5319 45.0901 86.4399 44.5264 88.3386 44.7112C90.034 45.1171 90.918 45.7276 92.1727 48.6661Z"
                          fill="#1EAA07"
                          stroke="#FDDBA9"
                        ></path>
                        <path
                          id="onion_2"
                          d="M70.8415 37.2587C68.5397 36.2211 68.0212 35.5697 68.0156 34.3249C68.6658 33.9214 69.0936 33.8629 70.0708 34.3249C71.1402 34.8474 71.783 35.5952 72.9609 37.2587C72.3132 38.9451 71.8954 39.8704 70.3919 41.2403C72.1607 42.4193 72.5374 44.3751 72.9609 44.3837C73.3844 44.3923 70.2313 48.9243 70.0708 49.9719C68.6618 50.0881 68.2293 49.8597 68.0156 48.994C67.8631 46.9998 68.8294 46.044 70.8415 44.3837C69.109 43.4403 68.3292 42.8249 68.0156 41.2403C67.9682 39.7728 68.3287 38.9206 70.8415 37.2587Z"
                          fill="#FFFBFB"
                          stroke="black"
                        ></path>
                      </g>
                      <g id="slice1">
                        <g id="slice_3">
                          <mask id="path-13-inside-3_7_2" fill="white">
                            <path
                              d="M138 79.5C138 88.5401 135.412 97.421 130.497 105.25C125.582 113.079 118.513 119.58 110 124.1L82 79.5H138Z"
                            ></path>
                          </mask>
                          <path
                            d="M138 79.5C138 88.5401 135.412 97.421 130.497 105.25C125.582 113.079 118.513 119.58 110 124.1L82 79.5H138Z"
                            fill="#FDDBA9"
                            stroke="#EE9758"
                            stroke-width="2"
                            mask="url(#path-13-inside-3_7_2)"
                          ></path>
                        </g>
                        <g id="pepperoni_3">
                          <circle cx="119" cy="99" r="6" fill="#F12424"></circle>
                          <circle cx="119" cy="99" r="6" fill="#F12424"></circle>
                        </g>
                        <path
                          id="pepper_3"
                          d="M110.227 89.6851C111.587 87.456 112.388 86.9817 113.864 87.0589C114.306 87.7349 114.352 88.166 113.749 89.1109C113.07 90.1438 112.147 90.7358 110.109 91.8011C108.145 91.0423 107.072 90.5634 105.532 88.9712C104.035 90.6587 101.695 90.9046 101.661 91.3269C101.627 91.7492 96.4305 88.2994 95.1975 88.0694C95.1387 86.6549 95.4337 86.2382 96.4722 86.0825C98.8451 86.063 99.9241 87.0914 101.78 89.2108C102.995 87.5439 103.769 86.8063 105.665 86.5986C107.408 86.6489 108.398 87.0656 110.227 89.6851Z"
                          fill="#1EAA07"
                          stroke="#FDDBA9"
                        ></path>
                        <path
                          id="onion_3"
                          d="M108.882 106.032C106.425 106.612 105.617 106.411 104.854 105.427C105.124 104.711 105.427 104.404 106.484 104.175C107.65 103.938 108.615 104.139 110.563 104.741C111.077 106.473 111.309 107.461 110.951 109.463C113.072 109.321 114.563 110.642 114.904 110.391C115.245 110.14 115.505 115.655 116.016 116.583C114.97 117.534 114.488 117.616 113.791 117.06C112.455 115.571 112.639 114.225 113.223 111.682C111.274 111.99 110.281 111.977 109.067 110.911C108.135 109.776 107.902 108.881 108.882 106.032Z"
                          fill="#FFFBFB"
                          stroke="black"
                        ></path>
                      </g>
                      <g id="slice2">
                        <g id="slice_4">
                          <mask id="path-17-inside-4_7_2" fill="white">
                            <path
                              d="M110 124.1C101.487 128.62 91.8301 131 82 131C72.1699 131 62.5131 128.62 54 124.1L82 79.5L110 124.1Z"
                            ></path>
                          </mask>
                          <path
                            d="M110 124.1C101.487 128.62 91.8301 131 82 131C72.1699 131 62.5131 128.62 54 124.1L82 79.5L110 124.1Z"
                            fill="#FDDBA9"
                            stroke="#EE9758"
                            stroke-width="2"
                            mask="url(#path-17-inside-4_7_2)"
                          ></path>
                        </g>
                        <g id="pepperoni_4">
                          <circle cx="78" cy="103" r="6" fill="#F12424"></circle>
                          <circle cx="78" cy="103" r="6" fill="#F12424"></circle>
                        </g>
                        <g id="mushroom_3">
                          <path
                            d="M86.3127 117.375C83.8388 116.35 83.5395 114.125 86.4349 108.925C90.8614 106.107 95.48 108.525 93.603 109.406C91.7261 110.288 91.5167 111.215 91.7805 111.398C91.7805 111.398 95.1264 113.286 94.9914 114.819C94.8563 116.353 93.7534 116.172 93.4095 116.548C93.0656 116.924 89.9579 113.391 89.9579 113.391C86.0194 116.126 88.7867 118.4 86.3127 117.375Z"
                            fill="#E3DDDD"
                          ></path>
                          <path
                            d="M89.9579 113.391C86.0194 116.126 88.7867 118.4 86.3127 117.375C83.8388 116.35 83.5395 114.125 86.4349 108.925C90.8614 106.107 95.48 108.525 93.603 109.406C91.7261 110.288 91.5167 111.215 91.7805 111.398M89.9579 113.391C89.9579 113.391 93.0656 116.924 93.4095 116.548C93.7534 116.172 94.8563 116.353 94.9914 114.819C95.1264 113.286 91.7805 111.398 91.7805 111.398M89.9579 113.391L91.7805 111.398"
                            stroke="black"
                          ></path>
                        </g>
                        <path
                          id="pepper_4"
                          d="M78.1727 124.666C79.9594 122.762 80.8409 122.462 82.27 122.84C82.5642 123.592 82.5204 124.023 81.7373 124.825C80.8608 125.697 79.8366 126.087 77.6233 126.713C75.857 125.568 74.9042 124.88 73.7226 123.006C71.9121 124.352 69.5712 124.114 69.4516 124.52C69.3319 124.926 64.9513 120.486 63.7915 120.009C64.0235 118.612 64.3975 118.265 65.4458 118.325C67.7725 118.791 68.6182 120.019 70.0009 122.473C71.5319 121.09 72.4399 120.526 74.3386 120.711C76.034 121.117 76.918 121.728 78.1727 124.666Z"
                          fill="#1EAA07"
                          stroke="#FDDBA9"
                        ></path>
                        <path
                          id="onion_4"
                          d="M84.2386 90.8992C81.7811 91.4786 80.9731 91.2779 80.2103 90.2943C80.4801 89.5782 80.7837 89.2712 81.8401 89.0422C83.0065 88.805 83.9717 89.0064 85.9193 89.608C86.4331 91.3399 86.6654 92.3282 86.3078 94.3305C88.4286 94.1878 89.9189 95.5092 90.26 95.258C90.6011 95.0069 90.8618 100.522 91.3727 101.45C90.3261 102.401 89.844 102.483 89.1471 101.927C87.8112 100.438 87.9952 99.0916 88.5793 96.5492C86.6308 96.8566 85.6375 96.8437 84.4234 95.7782C83.4917 94.6433 83.2584 93.7479 84.2386 90.8992Z"
                          fill="#FFFBFB"
                          stroke="black"
                        ></path>
                      </g>
                      <g id="slice4">
                        <g id="slice_5">
                          <mask id="path-23-inside-5_7_2" fill="white">
                            <path
                              d="M26 79.5C26 70.4599 28.5876 61.579 33.5026 53.75C38.4176 45.921 45.4869 39.4198 54 34.8997L82 79.5L26 79.5Z"
                            ></path>
                          </mask>
                          <path
                            d="M26 79.5C26 70.4599 28.5876 61.579 33.5026 53.75C38.4176 45.921 45.4869 39.4198 54 34.8997L82 79.5L26 79.5Z"
                            fill="#FDDBA9"
                            stroke="#EE9758"
                            stroke-width="2"
                            mask="url(#path-23-inside-5_7_2)"
                          ></path>
                        </g>
                        <g id="pepperoni_5">
                          <circle cx="64" cy="70" r="6" fill="#F12424"></circle>
                          <circle cx="64" cy="70" r="6" fill="#F12424"></circle>
                        </g>
                        <g id="mushroom_4">
                          <path
                            d="M43.3127 61.3748C40.8388 60.3499 40.5395 58.1249 43.4349 52.9246C47.8614 50.107 52.48 52.5248 50.603 53.4062C48.7261 54.2876 48.5167 55.215 48.7805 55.3984C48.7805 55.3984 52.1264 57.2856 51.9914 58.8193C51.8563 60.353 50.7534 60.1725 50.4095 60.5483C50.0656 60.9242 46.9579 57.3905 46.9579 57.3905C43.0194 60.1256 45.7867 62.3997 43.3127 61.3748Z"
                            fill="#E3DDDD"
                          ></path>
                          <path
                            d="M46.9579 57.3905C43.0194 60.1256 45.7867 62.3997 43.3127 61.3748C40.8388 60.3499 40.5395 58.1249 43.4349 52.9246C47.8614 50.107 52.48 52.5248 50.603 53.4062C48.7261 54.2876 48.5167 55.215 48.7805 55.3984M46.9579 57.3905C46.9579 57.3905 50.0656 60.9242 50.4095 60.5483C50.7534 60.1725 51.8563 60.353 51.9914 58.8193C52.1264 57.2856 48.7805 55.3984 48.7805 55.3984M46.9579 57.3905L48.7805 55.3984"
                            stroke="black"
                          ></path>
                        </g>
                        <path
                          id="pepper_5"
                          d="M57.8415 50.8697C55.5397 49.6375 55.0212 48.864 55.0156 47.3859C55.6658 46.9067 56.0936 46.8372 57.0708 47.3859C58.1402 48.0063 58.783 48.8943 59.9609 50.8697C59.3132 52.8724 58.8954 53.9711 57.3919 55.5979C59.1607 56.9979 59.5374 59.3204 59.9609 59.3306C60.3844 59.3409 57.2313 64.7227 57.0708 65.9666C55.6618 66.1046 55.2293 65.8334 55.0156 64.8053C54.8631 62.4372 55.8294 61.3022 57.8415 59.3306C56.109 58.2104 55.3292 57.4796 55.0156 55.5979C54.9682 53.8552 55.3287 52.8432 57.8415 50.8697Z"
                          fill="#1EAA07"
                          stroke="#FDDBA9"
                        ></path>
                        <path
                          id="onion_5"
                          d="M34.5084 66.9457C32.7549 68.7623 31.9667 69.0306 30.7931 68.6159C30.6326 67.8677 30.7219 67.4452 31.4866 66.6812C32.3393 65.8508 33.2601 65.4981 35.2235 64.9506C36.5925 66.1293 37.3225 66.8349 38.1047 68.7124C39.8113 67.4452 41.7796 67.7506 41.9306 67.3548C42.0816 66.959 45.2839 71.4564 46.2158 71.9611C45.8497 73.3266 45.4888 73.6567 44.6017 73.5657C42.673 73.0364 42.0994 71.8042 41.2154 69.3499C39.7428 70.6625 38.9003 71.1888 37.3029 70.9494C35.9054 70.4988 35.2248 69.8719 34.5084 66.9457Z"
                          fill="#FFFBFB"
                          stroke="black"
                        ></path>
                      </g>
                      <g id="slice3">
                        <g id="slice_6">
                          <mask id="path-29-inside-6_7_2" fill="white">
                            <path
                              d="M54 124.1C45.4869 119.58 38.4176 113.079 33.5026 105.25C28.5876 97.421 26 88.5401 26 79.5L82 79.5L54 124.1Z"
                            ></path>
                          </mask>
                          <path
                            d="M54 124.1C45.4869 119.58 38.4176 113.079 33.5026 105.25C28.5876 97.421 26 88.5401 26 79.5L82 79.5L54 124.1Z"
                            fill="#FDDBA9"
                            stroke="#EE9758"
                            stroke-width="2"
                            mask="url(#path-29-inside-6_7_2)"
                          ></path>
                        </g>
                        <g id="pepperoni_6">
                          <circle cx="42" cy="99" r="6" fill="#F12424"></circle>
                          <circle cx="42" cy="99" r="6" fill="#F12424"></circle>
                        </g>
                        <g id="mushroom_5">
                          <path
                            d="M57.3127 93.3748C54.8388 92.3499 54.5395 90.1249 57.4349 84.9246C61.8614 82.107 66.48 84.5248 64.603 85.4062C62.7261 86.2876 62.5167 87.215 62.7805 87.3984C62.7805 87.3984 66.1264 89.2856 65.9914 90.8193C65.8563 92.353 64.7534 92.1725 64.4095 92.5483C64.0656 92.9242 60.9579 89.3905 60.9579 89.3905C57.0194 92.1256 59.7867 94.3997 57.3127 93.3748Z"
                            fill="#E3DDDD"
                          ></path>
                          <path
                            d="M60.9579 89.3905C57.0194 92.1256 59.7867 94.3997 57.3127 93.3748C54.8388 92.3499 54.5395 90.1249 57.4349 84.9246C61.8614 82.107 66.48 84.5248 64.603 85.4062C62.7261 86.2876 62.5167 87.215 62.7805 87.3984M60.9579 89.3905C60.9579 89.3905 64.0656 92.9242 64.4095 92.5483C64.7534 92.1725 65.8563 92.353 65.9914 90.8193C66.1264 89.2856 62.7805 87.3984 62.7805 87.3984M60.9579 89.3905L62.7805 87.3984"
                            stroke="black"
                          ></path>
                        </g>
                        <path
                          id="pepper_6"
                          d="M45.1727 88.6661C46.9594 86.7623 47.8409 86.462 49.27 86.8398C49.5642 87.5919 49.5204 88.0231 48.7373 88.8247C47.8608 89.6968 46.8366 90.0874 44.6233 90.713C42.857 89.5684 41.9042 88.8801 40.7226 87.0063C38.9121 88.3518 36.5712 88.1136 36.4516 88.52C36.3319 88.9264 31.9513 84.4862 30.7915 84.0087C31.0235 82.6121 31.3975 82.2646 32.4458 82.3247C34.7725 82.7912 35.6182 84.0187 37.0009 86.473C38.5319 85.0901 39.4399 84.5264 41.3386 84.7112C43.034 85.1171 43.918 85.7276 45.1727 88.6661Z"
                          fill="#1EAA07"
                          stroke="#FDDBA9"
                        ></path>
                        <path
                          id="onion_6"
                          d="M53.4224 96.617C50.9625 96.0481 50.3269 95.5103 50.0787 94.2906C50.6377 93.7681 51.0459 93.6272 52.0944 93.8898C53.2452 94.1938 54.0214 94.8018 55.5011 96.2038C55.1947 97.9841 54.9652 98.9731 53.7578 100.61C55.7225 101.421 56.4733 103.266 56.8904 103.192C57.3074 103.118 55.0986 108.178 55.1454 109.236C53.7861 109.625 53.3173 109.486 52.9389 108.678C52.4005 106.752 53.1619 105.626 54.8116 103.605C52.9285 103.018 52.0437 102.566 51.4271 101.073C51.0944 99.6431 51.2818 98.737 53.4224 96.617Z"
                          fill="#FFFBFB"
                          stroke="black"
                        ></path>
                      </g>
                    </g>
                  </svg>
                </div>
              </div>
              <div v-else-if="!hasDietData" class="empty-data">
                <el-empty description="暂无今日饮食记录">
                  <el-button type="primary" @click="goToDietRecord">记录饮食</el-button>
                </el-empty>
              </div>
              <div v-else class="diet-list">
                <div v-for="(meal, index) in dietRecords" :key="index" class="diet-item">
                  <div class="diet-time">{{ meal.time }}</div>
                  <div class="diet-name">{{ meal.name }}</div>
                  <div class="diet-calories">{{ meal.calories }} 卡路里</div>
                </div>
              </div>
              <div class="card-footer">
                <el-button text @click="goToDietRecord">添加饮食记录</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
      
      <!-- 右侧边栏 -->
      <el-col :xs="24" :sm="24" :md="8" :lg="6">
        <UserProfileCard />

        <!-- 血糖监测卡片 -->
        <el-card class="glucose-card">
          <template #header>
            <div class="card-header">
              <span>血糖监测</span>
              <el-button type="text" @click="goToGlucoseRecord">
                查看更多
              </el-button>
            </div>
          </template>
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else>
            <!-- 血糖警报通知 -->
            <div v-if="glucoseAlerts.length > 0" class="glucose-alerts">
              <el-alert
                v-for="(alert, index) in glucoseAlerts"
                :key="index"
                :title="alert.title"
                :description="alert.message"
                :type="alert.type"
                :closable="true"
                show-icon
                @close="removeAlert(index)"
              />
            </div>
            
            <!-- 快速导入血糖数据 -->
            <div class="quick-import">
              <h4>快速记录血糖</h4>
              <el-form :model="glucoseForm" label-position="top" size="small">
                <el-form-item label="血糖值 (mmol/L)">
                  <el-input-number v-model="glucoseForm.value" :min="1" :max="30" :precision="1" :step="0.1" style="width: 100%" />
                </el-form-item>
                <el-form-item label="测量类型">
                  <el-select v-model="glucoseForm.measurement_time" placeholder="请选择" style="width: 100%">
                    <el-option label="早餐前" value="BEFORE_BREAKFAST" />
                    <el-option label="早餐后" value="AFTER_BREAKFAST" />
                    <el-option label="午餐前" value="BEFORE_LUNCH" />
                    <el-option label="午餐后" value="AFTER_LUNCH" />
                    <el-option label="晚餐前" value="BEFORE_DINNER" />
                    <el-option label="晚餐后" value="AFTER_DINNER" />
                    <el-option label="睡前" value="BEFORE_SLEEP" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="importGlucoseData" :loading="importing" style="width: 100%">
                    保存记录
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
            
            <!-- 新增：智能分析部分 -->
            <el-divider content-position="center">智能分析</el-divider>
            
            <div v-if="loadingAnalysis" class="loading-container">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="!hasAnalysisData" class="empty-analysis">
              <el-empty description="需要至少3天的血糖数据" :image-size="60">
                <template #description>
                  <p>需要更多血糖数据才能生成分析</p>
                </template>
                <el-button size="small" @click="fetchGlucoseAnalysis">尝试分析</el-button>
              </el-empty>
            </div>
            <div v-else class="glucose-analysis">
              <!-- 分析概要 -->
              <div class="analysis-summary">
                <div class="summary-item" :class="getValueClass(glucoseAnalysis.statistics.average)">
                  <div class="summary-value">{{ glucoseAnalysis.statistics.average.toFixed(1) }}</div>
                  <div class="summary-label">平均血糖</div>
                </div>
                <div class="summary-item" :class="getRangeClass(glucoseAnalysis.statistics.in_range_percentage)">
                  <div class="summary-value">{{ glucoseAnalysis.statistics.in_range_percentage.toFixed(0) }}%</div>
                  <div class="summary-label">达标率</div>
                </div>
                <div class="summary-item" :class="getStdClass(glucoseAnalysis.statistics.std)">
                  <div class="summary-value">{{ getVariabilityText(glucoseAnalysis.statistics.std) }}</div>
                  <div class="summary-label">波动性</div>
                </div>
              </div>
              
              <!-- 添加：AI预警信息展示区域 -->
              <div v-if="hasAnalysisData && glucoseAnalysis.advice" :class="['ai-alert-container', riskAssessmentStatus.class]">
                <div class="ai-alert-header">
                  <el-icon><component :is="riskAssessmentStatus.icon" /></el-icon>
                  <span>{{ riskAssessmentStatus.title }}</span>
                </div>
                <div class="ai-alert-content">
                  {{ truncateAdvice(glucoseAnalysis.advice, 120) }}
                </div>
                <el-button type="text" @click="showFullAdvice">查看完整分析</el-button>
              </div>
              
              <!-- 智能建议预览 -->
            </div>
          </div>
        </el-card>
        
        <!-- 今日提醒 -->
        <el-card class="reminder-card">
          <template #header>
            <div class="card-header">
              <span>今日提醒</span>
            </div>
          </template>
          <div class="reminder-list">
            <div v-for="(reminder, index) in reminders" :key="index" class="reminder-item">
              <el-icon :class="['reminder-icon', reminder.done ? 'done' : '']">
                <component :is="reminder.done ? 'CircleCheck' : 'Clock'" />
              </el-icon>
              <div class="reminder-content">
                <div class="reminder-text">{{ reminder.text }}</div>
                <div class="reminder-time">{{ reminder.time }}</div>
              </div>
              <el-checkbox v-model="reminder.done" @change="updateReminder(reminder)" />
            </div>
          </div>
        </el-card>
        
        <!-- 健康知识 -->
        <el-card class="knowledge-card">
          <template #header>
            <div class="card-header">
              <span>健康知识</span>
            </div>
          </template>
          <div class="knowledge-item" v-for="(article, index) in knowledgeArticles" :key="index">
            <div class="knowledge-title">{{ article.title }}</div>
            <div class="knowledge-desc">{{ article.description }}</div>
            <el-button text @click="readArticle(article.id)">阅读全文</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 新增：详细饮食建议卡片 (模态框) -->
    <div v-if="showDetailedAdviceCard" class="modal-overlay">
      <el-card class="detailed-advice-card modal-card">
        <template #header>
          <div class="card-header">
            <span>个性化饮食与血糖管理建议</span>
            <el-button type="danger" circle plain @click="showDetailedAdviceCard = false">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>
        <div class="advice-content-wrapper" v-html="detailedAdviceContent"></div>
      </el-card>
    </div>

    <!-- 新增：完整血糖分析卡片 (模态框) -->
    <div v-if="showFullAnalysisCard" class="modal-overlay">
      <el-card class="full-analysis-card modal-card">
        <template #header>
          <div class="card-header">
            <span>血糖风险评估与管理建议</span>
            <el-button type="danger" circle plain @click="showFullAnalysisCard = false">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>
        <div class="advice-content-wrapper" v-html="fullAnalysisContent"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onActivated, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { Plus, ChatLineRound, Clock, CircleCheck, Refresh, ChatLineSquare, InfoFilled, Warning, WarningFilled, Close } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { glucoseApi, healthApi, dietApi, knowledgeApi, apiClient } from '../api'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import UserProfileCard from '../components/UserProfileCard.vue'

const detailedAdviceContent = ref('')
const showDetailedAdviceCard = ref(false)

// 新增：用于"查看完整分析"模态框的状态
const fullAnalysisContent = ref('')
const showFullAnalysisCard = ref(false)

// 定义血糖记录类型接口
interface GlucoseRecord {
  id: string;
  value: number;
  measured_at: string;
  measurement_time: string;
  notes: string;
  user_id: string;
}

// 定义日期分组记录类型
interface DateGroupedRecords {
  [date: string]: {
    fasting: number[];
    afterMeal: number[];
  }
}

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const importing = ref(false)
const glucosePeriod = ref('week')
const glucoseChartRef = ref<HTMLElement | null>(null)
const glucoseChart = ref<echarts.ECharts | null>(null)
const chartKey = ref(0)
const glucoseCheckTimer = ref<number | null>(null)

const userName = computed(() => userStore.userFullName)
const currentDate = computed(() => dayjs().format('YYYY年MM月DD日'))

// 模拟数据
const healthMetrics = ref({
  weight: '68.5',
  bloodPressure: '120/80',
  bmi: '22.5',
  steps: '6,842'
})

const hasGlucoseData = ref(false)
const hasDietData = ref(true)
const glucoseAlerts = ref<Array<{title: string, message: string, type: 'success' | 'warning' | 'info' | 'error'}>>([])

const dietRecords = ref([
  { time: '早餐 08:30', name: '全麦面包+牛奶+鸡蛋', calories: 350 },
  { time: '午餐 12:00', name: '糙米饭+清蒸鱼+西兰花', calories: 480 },
  { time: '晚餐 18:30', name: '蔬菜沙拉+鸡胸肉', calories: 420 }
])

const reminders = ref([
  { id: 1, text: '测量空腹血糖', time: '早上8:00', done: true },
  { id: 2, text: '服用二甲双胍', time: '早餐后', done: true },
  { id: 3, text: '测量餐后血糖', time: '午餐后2小时', done: false },
  { id: 4, text: '30分钟有氧运动', time: '下午5:00', done: false },
  { id: 5, text: '服用二甲双胍', time: '晚餐后', done: false }
])

const knowledgeArticles = ref([
  {
    id: 1,
    title: '糖尿病患者如何科学运动',
    description: '适当的运动可以帮助控制血糖，但糖尿病患者需要注意一些事项...'
  },
  {
    id: 2,
    title: '低血糖的识别与处理',
    description: '低血糖是糖尿病患者常见的急性并发症，及时识别和处理非常重要...'
  },
  {
    id: 3,
    title: '糖尿病饮食的"四多四少"原则',
    description: '合理的饮食对控制血糖至关重要，建议多吃蔬菜、粗粮，少吃...'
  }
])

// 血糖数据
const glucoseRecords = ref<GlucoseRecord[]>([])

// 快速导入血糖表单
const glucoseForm = ref({
  value: 5.6,
  measurement_time: 'BEFORE_BREAKFAST'
})

// 智能分析相关状态
const loadingAnalysis = ref(false)
const hasAnalysisData = ref(false)
const glucoseAnalysis = ref({
  statistics: {
    average: 0,
    max: 0,
    min: 0,
    std: 0,
    in_range_percentage: 0,
    high_percentage: 0,
    low_percentage: 0
  },
  patterns: {},
  advice: '',
  risk_level: 'normal', // 新增风险等级: normal, warning, danger
  record_count: 0,
  updated_at: ''
})

// 饮食建议相关状态
const loadingDietSuggestions = ref(false)
const hasDietSuggestions = ref(false)
const selectedMealType = ref('breakfast')
const dietSuggestions = ref({
  current_status: '',
  glucose_status: 'normal', // 可能的值: high, normal, low
  quick_suggestion: '',
  recommended_foods: [] as string[],
  foods_to_avoid: [] as string[],
  meal_plan_example: ''
})

// 新增：风险评估状态计算属性
const riskAssessmentStatus = computed(() => {
  const level = glucoseAnalysis.value.risk_level
  if (level === 'danger') {
    return {
      class: 'ai-alert-danger',
      icon: WarningFilled,
      title: 'AI血糖高风险评估'
    }
  }
  if (level === 'warning') {
    return {
      class: 'ai-alert-warning',
      icon: Warning,
      title: 'AI血糖风险预警'
    }
  }
  return {
    class: 'ai-alert-good',
    icon: CircleCheck,
    title: 'AI血糖健康评估'
  }
})

// 从API获取血糖数据
const fetchGlucoseData = async () => {
  try {
    loading.value = true
    console.log('开始获取血糖数据...')
    
    // 使用新的API函数
    const response = await glucoseApi.getRecentGlucoseRecords(
      glucosePeriod.value === 'week' ? 7 : 30
    )
    
    console.log('获取到血糖数据:', response.data)
    
    if (Array.isArray(response.data)) {
      glucoseRecords.value = response.data
      hasGlucoseData.value = glucoseRecords.value.length > 0
      
      console.log(`获取到 ${glucoseRecords.value.length} 条血糖记录`)
      console.log('血糖记录示例:', glucoseRecords.value.slice(0, 2))
      
      // 返回数据状态，不在此函数中初始化图表
      return {
        success: true,
        hasData: hasGlucoseData.value
      }
    } else {
      console.error('API返回的数据格式不正确:', response.data)
      hasGlucoseData.value = false
      return {
        success: false,
        hasData: false
      }
    }
  } catch (error) {
    console.error('获取血糖数据失败', error)
    hasGlucoseData.value = false
    return {
      success: false,
      hasData: false
    }
  } finally {
    loading.value = false
  }
}

// 处理血糖数据，根据周期返回图表所需数据
const processGlucoseData = () => {
  console.log('开始处理血糖数据，当前记录数:', glucoseRecords.value?.length || 0)
  
  if (!glucoseRecords.value || glucoseRecords.value.length === 0) {
    console.log('没有血糖记录，返回空数据')
    return {
      dates: [] as string[],
      fastingData: [] as (number | null)[],
      afterMealData: [] as (number | null)[]
    }
  }
  
  // 根据周期过滤数据
  let filteredRecords = [...glucoseRecords.value]
  const now = dayjs()
  
  if (glucosePeriod.value === 'week') {
    // 获取最近7天的数据
    const startDate = now.subtract(6, 'day').startOf('day')
    console.log('周视图起始日期:', startDate.format('YYYY-MM-DD'))
    filteredRecords = filteredRecords.filter(record => 
      dayjs(record.measured_at).isAfter(startDate)
    )
  } else {
    // 获取最近30天的数据
    const startDate = now.subtract(29, 'day').startOf('day')
    console.log('月视图起始日期:', startDate.format('YYYY-MM-DD'))
    filteredRecords = filteredRecords.filter(record => 
      dayjs(record.measured_at).isAfter(startDate)
    )
  }
  
  console.log('过滤后的记录数:', filteredRecords.length)
  
  // 按日期分组
  const recordsByDate: DateGroupedRecords = {}
  const dateFormat = 'MM-DD'
  
  filteredRecords.forEach(record => {
    const date = dayjs(record.measured_at).format(dateFormat)
    if (!recordsByDate[date]) {
      recordsByDate[date] = {
        fasting: [],
        afterMeal: []
      }
    }
    
    // 根据测量时间类型分组
    if (['BEFORE_BREAKFAST', 'BEFORE_LUNCH', 'BEFORE_DINNER', 'before_breakfast', 'before_lunch', 'before_dinner'].includes(record.measurement_time.toUpperCase())) {
      recordsByDate[date].fasting.push(record.value)
    } else if (['AFTER_BREAKFAST', 'AFTER_LUNCH', 'AFTER_DINNER', 'after_breakfast', 'after_lunch', 'after_dinner'].includes(record.measurement_time.toUpperCase())) {
      recordsByDate[date].afterMeal.push(record.value)
    }
  })
  
  console.log('按日期分组后的数据:', recordsByDate)
  
  // 准备图表数据
  const dates: string[] = []
  const fastingData: (number | null)[] = []
  const afterMealData: (number | null)[] = []
  
  // 生成日期范围
  let dateRange: string[] = []
  if (glucosePeriod.value === 'week') {
    // 最近7天
    for (let i = 6; i >= 0; i--) {
      dateRange.push(now.subtract(i, 'day').format(dateFormat))
    }
  } else {
    // 最近30天
    for (let i = 29; i >= 0; i--) {
      dateRange.push(now.subtract(i, 'day').format(dateFormat))
    }
  }
  
  // 修复：使用新的dayjs实例避免日期计算错误
  dateRange = []
  const periodDays = glucosePeriod.value === 'week' ? 7 : 30
  const startDay = glucosePeriod.value === 'week' ? 6 : 29
  
  for (let i = startDay; i >= 0; i--) {
    const d = dayjs().subtract(i, 'day')
    dateRange.push(d.format(dateFormat))
  }
  
  console.log('生成的日期范围:', dateRange)
  
  // 填充数据，没有的日期用null
  dateRange.forEach(date => {
    dates.push(date)
    
    if (recordsByDate[date]) {
      // 计算空腹血糖平均值
      const fastingValues = recordsByDate[date].fasting
      fastingData.push(fastingValues.length > 0 
        ? Number((fastingValues.reduce((sum, val) => sum + val, 0) / fastingValues.length).toFixed(1))
        : null)
      
      // 计算餐后血糖平均值
      const afterMealValues = recordsByDate[date].afterMeal
      afterMealData.push(afterMealValues.length > 0
        ? Number((afterMealValues.reduce((sum, val) => sum + val, 0) / afterMealValues.length).toFixed(1))
        : null)
    } else {
      fastingData.push(null)
      afterMealData.push(null)
    }
  })
  
  console.log('处理后的图表数据:', {
    dates,
    fastingData,
    afterMealData
  })
  
  return { dates, fastingData, afterMealData }
}

// 快速导入血糖数据
const importGlucoseData = async () => {
  // 验证表单
  if (!glucoseForm.value.value || !glucoseForm.value.measurement_time) {
    ElMessage.warning('请填写完整的血糖数据')
    return
  }
  
  try {
    importing.value = true
    
    // 打印 userStore 以检查用户 ID 字段
    console.log('userStore:', userStore)
    
    // 检查用户ID是否存在
    if (!userStore.user || !userStore.user.id) {
      ElMessage.error('用户未登录或用户ID不存在')
      importing.value = false
      return
    }
    
    // 构建请求数据 - 确保格式正确
    const data = {
      value: glucoseForm.value.value,
      measured_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
      measurement_time: glucoseForm.value.measurement_time,
      measurement_method: 'FINGER_STICK', // 默认使用指尖血
      notes: '', // 添加可选的备注字段
      user_id: userStore.user.id // 添加用户ID
    }
    
    console.log('发送的血糖数据:', data)
    
    // 调用API保存血糖数据
    const response = await apiClient.post('/api/v1/glucose', data)
    
    console.log('保存血糖数据响应:', response)
    
    ElMessage.success('血糖数据保存成功')
    
    // 重置表单
    glucoseForm.value.value = 5.6
    
    // 刷新血糖数据
    await fetchGlucoseData()
    
    // 分析血糖数据
    await analyzeGlucoseData()
    
    // 获取三天分析
    await fetchGlucoseAnalysis()
    
  } catch (error) {
    console.error('保存血糖数据失败:', error)
    
    // 提供更详细的错误信息
    if (error.response) {
      console.error('错误响应数据:', error.response.data)
      
      // 显示详细的验证错误信息
      if (error.response.data && error.response.data.detail) {
        let errorMsg = '数据验证失败: ';
        
        if (Array.isArray(error.response.data.detail)) {
          errorMsg += error.response.data.detail.map(err => `${err.loc.join('.')}:${err.msg}`).join('; ');
        } else {
          errorMsg += error.response.data.detail;
        }
        
        ElMessage.error(errorMsg)
        return;
      }
    }
    
    ElMessage.error('保存血糖数据失败，请稍后再试')
  } finally {
    importing.value = false
  }
}

// 分析血糖数据
const analyzeGlucoseData = async () => {
  try {
    // 获取最近的血糖数据
    const recentResponse = await glucoseApi.getRecentGlucoseRecords(1); // 获取最近1天的数据
    
    if (!recentResponse.data || recentResponse.data.length === 0) {
      console.log('没有最近的血糖数据可供分析');
      return null;
    }
    
    const records = recentResponse.data;
    console.log('获取到最近的血糖数据:', records);
    
    // 调用后端分析API获取血糖异常预警
    try {
      const analyzeResponse = await apiClient.post('/api/v1/glucose-monitor/analyze', {
        hours: 24 // 分析最近24小时的数据
      }, {
        timeout: 20000 // 设置20秒超时时间
      });
      
      // 处理API返回的预警信息
      if (analyzeResponse.data?.has_alerts) {
        // 如果有预警信息并且包含大模型生成的警报消息
        if (analyzeResponse.data.alert_message) {
          // 清除现有的相似警报
          glucoseAlerts.value = glucoseAlerts.value.filter(alert => !alert.title.includes('血糖异常'));
          
          // 添加新的警报，显示大模型生成的个性化预警信息
          addAlert(
            '血糖异常预警', 
            analyzeResponse.data.alert_message, 
            analyzeResponse.data.alerts.some(a => a.severity === 'high') ? 'error' : 'warning'
          );
          console.log('添加大模型生成的预警消息:', analyzeResponse.data.alert_message);
          
          return {
            statistics: analyzeResponse.data.statistics || {
              average: 0,
              max: 0,
              min: 0,
              count: records.length,
              high_count: 0,
              low_count: 0
            },
            has_alerts: true,
            alert_message: analyzeResponse.data.alert_message
          };
        }
      }
    } catch (apiError) {
      console.error('调用血糖分析API失败，回退到本地分析:', apiError);
      // 发生错误时继续使用本地分析
    }
    
    // 本地分析血糖数据（作为备选方案）
    const highThreshold = 7.8; // 高血糖阈值
    const lowThreshold = 3.9; // 低血糖阈值
    
    const highRecords = records.filter(record => record.value > highThreshold);
    const lowRecords = records.filter(record => record.value < lowThreshold);
    
    // 生成警报
    if (highRecords.length > 0 || lowRecords.length > 0) {
      let alertMessage = '';
      
      if (highRecords.length > 0) {
        const latestHigh = highRecords.sort((a, b) => 
          new Date(b.measured_at).getTime() - new Date(a.measured_at).getTime()
        )[0];
        
        alertMessage += `检测到${highRecords.length}次高血糖记录，最近一次为${dayjs(latestHigh.measured_at).format('MM-DD HH:mm')}，血糖值${latestHigh.value.toFixed(1)}mmol/L。`;
      }
      
      if (lowRecords.length > 0) {
        if (alertMessage) alertMessage += ' ';
        
        const latestLow = lowRecords.sort((a, b) => 
          new Date(b.measured_at).getTime() - new Date(a.measured_at).getTime()
        )[0];
        
        alertMessage += `检测到${lowRecords.length}次低血糖记录，最近一次为${dayjs(latestLow.measured_at).format('MM-DD HH:mm')}，血糖值${latestLow.value.toFixed(1)}mmol/L。`;
      }
      
      // 添加警报
      if (alertMessage) {
        addAlert('血糖异常提醒', alertMessage, 'warning');
      }
    }
    
    // 计算统计数据
    const sum = records.reduce((acc, record) => acc + record.value, 0);
    const avg = sum / records.length;
    const max = Math.max(...records.map(record => record.value));
    const min = Math.min(...records.map(record => record.value));
    
    return {
      statistics: {
        average: avg,
        max: max,
        min: min,
        count: records.length,
        high_count: highRecords.length,
        low_count: lowRecords.length
      },
      has_alerts: highRecords.length > 0 || lowRecords.length > 0
    };
  } catch (error) {
    console.error('分析血糖数据失败:', error);
    return null;
  }
}

// 添加警报
const addAlert = (title: string, message: string, type: 'success' | 'warning' | 'info' | 'error' = 'warning') => {
  glucoseAlerts.value.push({
    title,
    message,
    type
  })
}

// 移除警报
const removeAlert = (index: number) => {
  glucoseAlerts.value.splice(index, 1)
}

// 组件挂载时初始化
onMounted(async () => {
  try {
    // 获取血糖数据
    const glucoseResult = await fetchGlucoseData()
    
    // 如果有血糖数据，分析血糖数据
    if (glucoseResult?.hasData) {
      await analyzeGlucoseData()
      await fetchGlucoseAnalysis()
    }
    
    // 确保DOM已更新
    await nextTick()
    
    // 初始化图表
    if (hasGlucoseData.value) {
      initGlucoseChart()
    }
    
    // 设置定时检查血糖数据的定时器（每30分钟检查一次）
    const checkInterval = 30 * 60 * 1000; // 30分钟
    glucoseCheckTimer.value = setInterval(async () => {
      console.log('定时检查血糖数据...');
      await analyzeGlucoseData();
    }, checkInterval);
    
    // 如果有血糖数据，获取饮食建议
    if (glucoseResult?.hasData) {
      await fetchDietSuggestions()
    }
    
  } catch (error) {
    console.error('初始化数据失败:', error)
    ElMessage.error('加载数据失败，请刷新页面重试')
  } finally {
    loading.value = false
  }
})

// 在组件卸载时清除定时器
onUnmounted(() => {
  if (glucoseCheckTimer.value) {
    clearInterval(glucoseCheckTimer.value);
    glucoseCheckTimer.value = null;
  }
})

// 添加onActivated钩子，在组件被激活时重新获取数据
onActivated(async () => {
  console.log('Dashboard组件被激活，重新获取数据')
  try {
    // 检查图表是否已初始化
    if (hasGlucoseData.value && !glucoseChart.value && glucoseChartRef.value) {
      console.log('组件激活，但图表未初始化，尝试初始化图表')
      
      // 更新chartKey强制重新渲染图表容器
      chartKey.value += 1
      
      await nextTick()
      
      // 强制设置容器尺寸
      if (glucoseChartRef.value) {
        glucoseChartRef.value.style.height = '300px'
        glucoseChartRef.value.style.width = '100%'
      }
      
      setTimeout(() => {
        initGlucoseChart()
      }, 200)
    } else if (!glucoseChart.value) {
      // 重新获取数据
      const result = await fetchGlucoseData()
      
      if (result.success && result.hasData) {
        // 更新chartKey强制重新渲染图表容器
        chartKey.value += 1
        
        await nextTick()
        
        // 强制设置容器尺寸
        if (glucoseChartRef.value) {
          glucoseChartRef.value.style.height = '300px'
          glucoseChartRef.value.style.width = '100%'
        }
        
        setTimeout(() => {
          initGlucoseChart()
        }, 200)
      }
    } else {
      console.log('图表已存在，尝试更新')
      updateGlucoseChart()
    }
    
    // 刷新饮食建议
    if (hasGlucoseData.value && !hasDietSuggestions.value) {
      await fetchDietSuggestions()
    }
  } catch (error) {
    console.error('重新获取血糖数据失败', error)
  } finally {
    loading.value = false
  }
})

// 添加手动刷新功能
const refreshData = async () => {
  try {
    loading.value = true
    console.log('手动刷新数据开始')
    
    // 销毁现有图表实例
    if (glucoseChart.value) {
      console.log('销毁现有图表实例')
      glucoseChart.value.dispose()
      glucoseChart.value = null
    }
    
    // 更新chartKey强制重新渲染图表容器
    chartKey.value += 1
    console.log('更新chartKey:', chartKey.value)
    
    // 获取新数据
    const result = await fetchGlucoseData()
    
    // 确保在获取数据后重新创建图表
    if (result.success && result.hasData) {
      console.log('刷新后准备重新创建图表')
      
      // 使用更简单的方法，直接重新创建图表
      await nextTick()
      
      // 确保图表容器存在
      if (!glucoseChartRef.value) {
        console.error('图表容器不存在，无法重新创建图表')
        return
      }
      
      // 强制设置容器尺寸
      glucoseChartRef.value.style.height = '300px'
      glucoseChartRef.value.style.width = '100%'
      
      console.log('重新创建图表实例')
      try {
        // 确保echarts已正确导入
        if (!echarts) {
          console.error('echarts库未正确导入')
          return
        }
        
        // 直接创建新实例
        glucoseChart.value = echarts.init(glucoseChartRef.value)
        console.log('图表实例创建成功:', glucoseChart.value)
        
        // 设置图表选项
        updateGlucoseChart()
      } catch (error) {
        console.error('刷新时创建图表实例失败:', error)
      }
    }
    
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败', error)
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

// 监听glucosePeriod变化，更新图表
watch(glucosePeriod, () => {
  if (hasGlucoseData.value && glucoseChart.value) {
    updateGlucoseChart()
  }
})

// 更新血糖图表
const updateGlucoseChart = () => {
  console.log('开始更新图表')
  if (!glucoseChart.value) {
    console.error('图表实例不存在，无法更新')
    return
  }
  
  const { dates, fastingData, afterMealData } = processGlucoseData()
  console.log('处理后的图表数据:', { 
    dates, 
    fastingData, 
    afterMealData,
    datesLength: dates.length
  })
  
  try {
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params: any) {
          let result = params[0].axisValueLabel + '<br/>';
          params.forEach((param: any) => {
            if (param.value !== null) {
              const color = param.value > 7.8 ? '#f56c6c' : 
                            param.value < 3.9 ? '#e6a23c' : '#67c23a';
              result += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>`;
              result += `${param.seriesName}: <span style="color:${color};font-weight:bold">${param.value} mmol/L</span><br/>`;
            }
          });
          return result;
        }
      },
      legend: {
        data: ['空腹血糖', '餐后血糖']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '血糖 (mmol/L)',
        min: 3, // 调整范围以获得更好的视觉效果
        max: 12,
        interval: 1.5,
        axisLine: { lineStyle: { color: '#aaa' } },
        splitLine: {
          lineStyle: {
            color: '#eee'
          }
        }
      },
      series: [
        {
          name: '空腹血糖',
          type: 'line',
          smooth: true, // 使线条更平滑
          data: fastingData,
          connectNulls: true,
          symbol: 'circle',
          symbolSize: 8, // 稍大的标记点
          itemStyle: {
            color: '#3498db' // 活力蓝
          },
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(52, 152, 219, 0.5)',
            shadowBlur: 10,
            shadowOffsetY: 5
          },
          markArea: {
            itemStyle: {
              color: 'rgba(46, 204, 113, 0.1)' // 清新绿
            },
            data: [
              [{
                yAxis: 3.9
              }, {
                yAxis: 6.1
              }]
            ]
          }
        },
        {
          name: '餐后血糖',
          type: 'line',
          smooth: true, // 使线条更平滑
          data: afterMealData,
          connectNulls: true,
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: {
            color: '#e67e22' // 活力橙
          },
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(230, 126, 34, 0.5)',
            shadowBlur: 10,
            shadowOffsetY: 5
          },
          markArea: {
            itemStyle: {
              color: 'rgba(46, 204, 113, 0.1)' // 清新绿
            },
            data: [
              [{
                yAxis: 3.9
              }, {
                yAxis: 7.8
              }]
            ]
          }
        }
      ]
    }
    
    console.log('设置图表选项')
    glucoseChart.value.setOption(option)
    console.log('图表选项设置完成')
  } catch (error) {
    console.error('设置图表选项失败:', error)
  }
}

const initGlucoseChart = () => {
  console.log('开始初始化图表')
  console.log('glucoseChartRef元素:', glucoseChartRef.value)
  
  if (!glucoseChartRef.value) {
    console.error('图表容器元素不存在，无法初始化图表')
    return
  }
  
  // 如果已经有图表实例，先销毁
  if (glucoseChart.value) {
    console.log('销毁旧图表实例')
    try {
      glucoseChart.value.dispose()
    } catch (error) {
      console.error('销毁旧图表实例失败:', error)
    }
    glucoseChart.value = null
  }
  
  // 确保DOM元素有宽高
  const chartElement = glucoseChartRef.value
  if (chartElement.offsetHeight === 0) {
    console.log('图表容器高度为0，设置默认高度')
    chartElement.style.height = '300px'
  }
  
  if (chartElement.offsetWidth === 0) {
    console.log('图表容器宽度为0，设置默认宽度')
    chartElement.style.width = '100%'
  }
  
  console.log('图表容器尺寸:', {
    height: chartElement.offsetHeight,
    width: chartElement.offsetWidth,
    clientHeight: chartElement.clientHeight,
    clientWidth: chartElement.clientWidth
  })
  
  // 创建新的图表实例
  try {
    console.log('创建新图表实例')
    // 确保echarts已正确导入
    if (!echarts) {
      console.error('echarts库未正确导入')
      return
    }
    
    glucoseChart.value = echarts.init(chartElement)
    console.log('图表实例创建成功:', glucoseChart.value)
    
    // 设置图表选项
    updateGlucoseChart()
    
    // 监听窗口大小变化，调整图表大小
    const resizeHandler = () => {
      console.log('窗口大小变化，调整图表大小')
      if (glucoseChart.value) {
        glucoseChart.value.resize()
      }
    }
    
    window.removeEventListener('resize', resizeHandler)
    window.addEventListener('resize', resizeHandler)
  } catch (error) {
    console.error('图表初始化失败:', error)
    // 尝试再次初始化
    setTimeout(() => {
      console.log('尝试再次初始化图表')
      try {
        if (chartElement && !glucoseChart.value) {
          glucoseChart.value = echarts.init(chartElement)
          updateGlucoseChart()
        }
      } catch (retryError) {
        console.error('再次初始化图表失败:', retryError)
      }
    }, 500)
  }
}

const updateReminder = (reminder: any) => {
  // 这里应该调用API更新提醒状态
  console.log('更新提醒状态', reminder)
}

const readArticle = (id: number) => {
  router.push(`/knowledge/${id}`)
}

const goToGlucoseRecord = () => {
  router.push('/glucose-record')
}

const goToAssistant = () => {
  router.push('/assistant')
}

const goToHealthData = () => {
  router.push('/health')
}

const goToDietRecord = () => {
  router.push('/diet')
}

// 获取血糖智能分析
const fetchGlucoseAnalysis = async () => {
  if (!hasGlucoseData.value) return

  try {
    loadingAnalysis.value = true
    
    // 获取最近记录的血糖数据
    const recentResponse = await glucoseApi.getRecentGlucoseRecords(3)
    
    if (!recentResponse.data || recentResponse.data.length < 3) {
      hasAnalysisData.value = false
      loadingAnalysis.value = false
      return
    }
    
    // 使用后端分析API获取血糖异常预警和统计数据
    const analyzeResponse = await apiClient.post('/api/v1/glucose-monitor/analyze', {
      hours: 72 // 分析最近72小时(3天)的数据
    }, {
      timeout: 30000 // 设置30秒超时时间
    })
    
    // 确定风险等级
    let riskLevel: 'normal' | 'warning' | 'danger' = 'normal'
    if (analyzeResponse.data?.has_alerts && analyzeResponse.data.alerts?.length > 0) {
      if (analyzeResponse.data.alerts.some(a => a.severity === 'high')) {
        riskLevel = 'danger'
      } else {
        riskLevel = 'warning'
      }
    }
    
    // 如果有预警信息，显示在顶部警报区域
    if (analyzeResponse.data?.has_alerts && analyzeResponse.data?.alert_message) {
      // 清除现有的相似警报
      glucoseAlerts.value = glucoseAlerts.value.filter(alert => !alert.title.includes('血糖异常'))
      
      // 添加新的警报，显示大模型生成的个性化预警信息
      addAlert(
        '血糖异常预警', 
        analyzeResponse.data.alert_message, 
        analyzeResponse.data.alerts.some(a => a.severity === 'high') ? 'error' : 'warning'
      )
    }
    
    // 获取统计数据
    const statsResponse = await glucoseApi.getStatistics('week')
    
    if (statsResponse.data) {
      // 构建分析数据结构
      const records = recentResponse.data
      const stats = statsResponse.data
      
      // 计算标准差
      let sum = 0
      let sumSquares = 0
      records.forEach(record => {
        sum += record.value
        sumSquares += record.value * record.value
      })
      const mean = sum / records.length
      const variance = sumSquares / records.length - mean * mean
      const std = Math.sqrt(variance)
      
      // 计算达标率
      const inRangeCount = records.filter(r => r.value >= 3.9 && r.value <= 7.8).length
      const inRangePercentage = (inRangeCount / records.length) * 100
      
      // 计算高低血糖比例
      const highCount = records.filter(r => r.value > 7.8).length
      const lowCount = records.filter(r => r.value < 3.9).length
      const highPercentage = (highCount / records.length) * 100
      const lowPercentage = (lowCount / records.length) * 100
      
      // 优先使用大模型生成的建议
      let advice = ''
      
      // 判断是否有可用的大模型生成的建议
      if (analyzeResponse.data?.alert_message) {
        // 使用大模型生成的个性化预警建议
        advice = analyzeResponse.data.alert_message
        console.log('使用大模型生成的预警建议:', advice)
      } else {
        // 生成本地建议文本
        advice = '根据您最近三天的血糖记录分析：\n\n'
        
        if (mean > 7.8) {
          advice += '您的平均血糖偏高，建议控制碳水化合物摄入，增加运动量。\n\n'
        } else if (mean < 3.9) {
          advice += '您的平均血糖偏低，请注意及时补充碳水化合物，避免低血糖发生。\n\n'
        } else {
          advice += '您的平均血糖处于正常范围，请继续保持良好的生活方式。\n\n'
        }
        
        if (std > 2.0) {
          advice += '您的血糖波动较大，建议规律三餐，避免暴饮暴食，监测血糖的频率可以适当增加。\n\n'
        }
        
        if (inRangePercentage < 70) {
          advice += `您的血糖达标率为${inRangePercentage.toFixed(0)}%，低于理想水平(70%)，建议咨询医生调整治疗方案。\n\n`;
        } else if (riskLevel === 'normal') {
          advice = '您的血糖控制良好，各项指标均在理想范围内。请继续保持当前的健康生活方式，定期监测，预防风险。'
        } else {
          advice += '请记住，良好的饮食习惯、适当的运动和按时服药是控制血糖的关键。'
        }
      }
      
      // 更新分析数据
      glucoseAnalysis.value = {
        statistics: {
          average: mean,
          max: stats.max_value || 0,
          min: stats.min_value || 0,
          std: std,
          in_range_percentage: inRangePercentage,
          high_percentage: highPercentage,
          low_percentage: lowPercentage
        },
        patterns: {
          fasting_avg: records.filter(r => 
            ['BEFORE_BREAKFAST', 'BEFORE_LUNCH', 'BEFORE_DINNER'].includes(r.measurement_time)
          ).reduce((sum, r) => sum + r.value, 0) / 
          Math.max(1, records.filter(r => 
            ['BEFORE_BREAKFAST', 'BEFORE_LUNCH', 'BEFORE_DINNER'].includes(r.measurement_time)
          ).length),
          postprandial_avg: records.filter(r => 
            ['AFTER_BREAKFAST', 'AFTER_LUNCH', 'AFTER_DINNER'].includes(r.measurement_time)
          ).reduce((sum, r) => sum + r.value, 0) / 
          Math.max(1, records.filter(r => 
            ['AFTER_BREAKFAST', 'AFTER_LUNCH', 'AFTER_DINNER'].includes(r.measurement_time)
          ).length)
        },
        advice: advice,
        risk_level: riskLevel, // 设置风险等级
        record_count: records.length,
        updated_at: new Date().toISOString()
      }
      
      hasAnalysisData.value = true
    } else {
      hasAnalysisData.value = false
      ElMessage.info('暂无足够的血糖数据进行分析')
    }
  } catch (error) {
    console.error('获取血糖分析失败:', error)
    ElMessage.error('获取血糖分析失败，请稍后再试')
    hasAnalysisData.value = false
  } finally {
    loadingAnalysis.value = false
  }
}

// 获取饮食建议
const fetchDietSuggestions = async () => {
  if (!hasGlucoseData.value) {
    ElMessage.warning('需要血糖数据才能生成饮食建议')
    return
  }
  
  try {
    loadingDietSuggestions.value = true
    
    // 暂时移除大模型API调用，直接使用模拟数据
    // const latestGlucose = glucoseRecords.value[0]?.value || 0
    // const isMealTime = new Date().getHours() >= 6 && new Date().getHours() <= 20
    // const isBeforeMeal = isMealTime && Math.random() > 0.5
    
    // 不再调用API，直接使用模拟数据
    // const response = await apiClient.get('/api/v1/glucose-monitor/quick-diet-suggestions', {
    //   params: {
    //     glucose_value: latestGlucose,
    //     meal_type: selectedMealType.value,
    //     is_before_meal: isBeforeMeal
    //   }
    // })
    
    // 直接使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 500)) // 模拟延迟
    simulateDietSuggestions()
    
  } catch (error) {
    console.error('获取饮食建议失败:', error)
    // 出错时也使用模拟数据
    simulateDietSuggestions()
  } finally {
    loadingDietSuggestions.value = false
  }
}

// 模拟饮食建议数据（在API未实现时使用）
const simulateDietSuggestions = () => {
  const latestGlucose = glucoseRecords.value[0]?.value || 7.2
  const isBeforeMeal = Math.random() > 0.5
  const status = getGlucoseStatus(latestGlucose, isBeforeMeal)
  
  let suggestion = ''
  let recommended: string[] = []
  let avoid: string[] = []
  let mealPlan = ''
  
  if (status === 'high') {
    suggestion = '您的血糖偏高，建议减少碳水化合物摄入，增加蛋白质和膳食纤维。'
    recommended = ['蔬菜沙拉', '鸡胸肉', '豆腐', '牛油果', '坚果少量']
    avoid = ['白米饭', '白面包', '甜点', '含糖饮料']
    mealPlan = '推荐：烤鸡胸肉100g + 混合蔬菜沙拉 + 藜麦50g'
  } else if (status === 'low') {
    suggestion = '您的血糖偏低，建议适量摄入优质碳水化合物，避免空腹过久。'
    recommended = ['全麦面包', '燕麦', '香蕉', '酸奶', '蜂蜜少量']
    avoid = ['精制糖', '果汁', '咖啡因饮料']
    mealPlan = '推荐：全麦面包2片 + 煮鸡蛋1个 + 小香蕉1根'
  } else {
    suggestion = '您的血糖正常，建议保持均衡饮食，控制碳水化合物摄入量。'
    recommended = ['全谷物', '绿叶蔬菜', '鱼肉', '豆制品', '坚果适量']
    avoid = ['精制碳水', '甜点', '油炸食品']
    mealPlan = '推荐：糙米饭半碗 + 清蒸鱼100g + 西兰花 + 豆腐'
  }
  
  dietSuggestions.value = {
    current_status: `您的当前血糖为${latestGlucose.toFixed(1)} mmol/L，属于${isBeforeMeal ? '餐前' : '餐后'}${status === 'normal' ? '正常' : status === 'high' ? '偏高' : '偏低'}范围。`,
    glucose_status: status,
    quick_suggestion: suggestion,
    recommended_foods: recommended,
    foods_to_avoid: avoid,
    meal_plan_example: mealPlan
  }
  
  hasDietSuggestions.value = true
}

// 根据血糖值判断状态
const getGlucoseStatus = (value: number, isBeforeMeal: boolean): 'high' | 'normal' | 'low' => {
  if (isBeforeMeal) {
    if (value < 3.9) return 'low'
    if (value > 7.0) return 'high'
    return 'normal'
  } else {
    if (value < 3.9) return 'low'
    if (value > 10.0) return 'high'
    return 'normal'
  }
}

// 获取饮食状态对应的CSS类
const getDietStatusClass = (status: string) => {
  if (status === 'high') return 'status-high'
  if (status === 'low') return 'status-low'
  return 'status-normal'
}

// 刷新饮食建议
const refreshDietSuggestions = () => {
  fetchDietSuggestions()
}

// 更新餐食建议
const updateMealSuggestion = async () => {
  try {
    loadingDietSuggestions.value = true
    
    // 在实际应用中，这里应该调用API获取特定餐食类型的建议
    // 这里使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const mealPlans = {
      breakfast: '早餐推荐：全麦面包2片 + 煮鸡蛋1个 + 牛奶200ml',
      lunch: '午餐推荐：糙米饭半碗 + 清蒸鱼100g + 西兰花 + 豆腐',
      dinner: '晚餐推荐：藜麦沙拉 + 烤鸡胸肉100g + 烤红薯小份',
      snack: '加餐推荐：无糖酸奶100g + 蓝莓一小把或坚果10g'
    }
    
    dietSuggestions.value.meal_plan_example = mealPlans[selectedMealType.value]
  } catch (error) {
    console.error('更新餐食建议失败:', error)
  } finally {
    loadingDietSuggestions.value = false
  }
}

// 显示详细饮食建议
const showDetailedDietSuggestions = async () => {
  try {
    ElMessage.info('正在生成详细饮食建议...')
    
    const response = await apiClient.post('/api/v1/glucose-monitor/analyze-trend', { days: 3 }, {
      timeout: 30000 
    })
    
    if (!response.data || !response.data.advice) {
      throw new Error('无法获取血糖分析和建议')
    }
    
    const adviceContent = response.data.advice
    
    let processedAdvice = adviceContent
      .replace(/\n\n/g, '<br><br>')
      .replace(/###\s+(.*?)(\n|$)/g, '<h3>$1</h3>')
      .replace(/####\s+(.*?)(\n|$)/g, '<h4>$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    
    detailedAdviceContent.value = `
      <div class="blood-glucose-analysis">
        ${processedAdvice}
      </div>
      <h4 class="additional-meal-suggestions">根据您选择的餐型，我们提供以下建议</h4>
      <p><strong>${selectedMealType.value === 'breakfast' ? '早餐' : 
                    selectedMealType.value === 'lunch' ? '午餐' : 
                    selectedMealType.value === 'dinner' ? '晚餐' : '加餐'}</strong>：
         <span style="color:#409EFF">${dietSuggestions.value.meal_plan_example}</span>
      </p>
    `
    showDetailedAdviceCard.value = true
  } catch (error) {
    console.error('获取详细饮食建议失败:', error)
    ElMessage.error('获取详细饮食建议失败，请稍后再试')
    
    fallbackToLocalSuggestions()
  }
}

// 回退到本地静态建议
const fallbackToLocalSuggestions = () => {
  const detailedSuggestion = `
    <h3>个性化饮食建议</h3>
    <p>基于您的血糖数据分析，我们为您提供以下饮食建议：</p>
    
    <h4>总体原则</h4>
    <ul>
      <li>控制碳水化合物总量，选择低GI值的碳水食物</li>
      <li>增加蛋白质和健康脂肪的摄入</li>
      <li>多吃富含膳食纤维的蔬菜</li>
      <li>规律三餐，避免长时间空腹</li>
    </ul>
    
    <h4>推荐食物清单</h4>
    <ul>
      <li><strong>碳水来源</strong>：全麦面包、燕麦、糙米、藜麦、红薯</li>
      <li><strong>蛋白质来源</strong>：鸡胸肉、鱼、豆腐、鸡蛋、希腊酸奶</li>
      <li><strong>健康脂肪</strong>：牛油果、橄榄油、坚果(适量)</li>
      <li><strong>蔬菜水果</strong>：西兰花、菠菜、芦笋、蓝莓、草莓(适量)</li>
    </ul>
    
    <h4>一日三餐建议</h4>
    <p><strong>早餐</strong>：${selectedMealType.value === 'breakfast' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '全麦面包2片 + 煮鸡蛋1个 + 牛奶200ml'}</p>
    <p><strong>午餐</strong>：${selectedMealType.value === 'lunch' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '糙米饭半碗 + 清蒸鱼100g + 西兰花 + 豆腐'}</p>
    <p><strong>晚餐</strong>：${selectedMealType.value === 'dinner' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '藜麦沙拉 + 烤鸡胸肉100g + 烤红薯小份'}</p>
    <p><strong>加餐</strong>：${selectedMealType.value === 'snack' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '无糖酸奶100g + 蓝莓一小把或坚果10g'}</p>
  `
  detailedAdviceContent.value = detailedSuggestion
  showDetailedAdviceCard.value = true
}

// 辅助方法：根据血糖值获取CSS类
const getValueClass = (value) => {
  if (value > 10.0) return 'high-value'
  if (value < 3.9) return 'low-value'
  return 'normal-value'
}

// 辅助方法：根据达标率获取CSS类
const getRangeClass = (percentage) => {
  if (percentage >= 70) return 'good-range'
  if (percentage >= 50) return 'average-range'
  return 'poor-range'
}

// 辅助方法：根据标准差获取CSS类
const getStdClass = (std) => {
  if (std <= 1.5) return 'stable-std'
  if (std <= 2.5) return 'moderate-std'
  return 'unstable-std'
}

// 辅助方法：根据标准差获取波动性描述
const getVariabilityText = (std) => {
  if (std <= 1.5) return '稳定'
  if (std <= 2.5) return '一般'
  return '波动大'
}

// 截断建议文本，显示预览
const truncateAdvice = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 显示完整建议
const showFullAdvice = async () => {
  try {
    // 显示加载提示
    ElMessage.info('正在获取最新的血糖风险评估...')
    
    // 首先调用analyze接口获取预警信息
    const alertResponse = await apiClient.post('/api/v1/glucose-monitor/analyze', {
      hours: 72 // 分析最近72小时的数据
    }, {
      timeout: 30000 // 设置30秒超时时间
    })
    
    // 然后调用analyze-trend接口获取详细的血糖分析报告
    const trendResponse = await apiClient.post('/api/v1/glucose-monitor/analyze-trend', { 
      days: 3 
    }, {
      timeout: 30000 // 设置30秒超时时间
    })
    
    if (!trendResponse.data || !trendResponse.data.advice) {
      throw new Error('无法获取血糖分析和建议')
    }
    
    // 使用大模型生成的血糖分析报告和建议
    const adviceContent = trendResponse.data.advice
    let dialogTitle = '血糖风险评估与管理建议'
    
    // 更新当前的建议内容
    glucoseAnalysis.value.advice = adviceContent
    
    // 如果有预警信息，添加到顶部警报区域
    if (alertResponse.data?.has_alerts && alertResponse.data?.alert_message) {
      // 清除现有的相似警报
      glucoseAlerts.value = glucoseAlerts.value.filter(alert => !alert.title.includes('血糖异常'))
      
      // 添加新的警报，显示大模型生成的个性化预警信息
      addAlert(
        '血糖异常预警', 
        alertResponse.data.alert_message, 
        alertResponse.data.alerts.some(a => a.severity === 'high') ? 'error' : 'warning'
      )
    }
    
    // 将大模型生成的文本处理为HTML格式
    let processedAdvice = adviceContent
      .replace(/\n\n/g, '<br><br>') // 替换双换行为HTML换行
      .replace(/###\s+(.*?)(\n|$)/g, '<h3>$1</h3>') // 处理 ### 标题
      .replace(/####\s+(.*?)(\n|$)/g, '<h4>$1</h4>') // 处理 #### 标题
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // 处理加粗文本
    
    // 如果有预警信息，在分析报告前添加预警信息
    let contentToShow = ``
    
    if (alertResponse.data?.has_alerts && alertResponse.data?.alert_message) {
      contentToShow = `
        <div class="glucose-alert-warning">
          <h3>⚠️ 血糖异常预警</h3>
          <p>${alertResponse.data.alert_message}</p>
        </div>
        <div class="blood-glucose-analysis ai-analysis-content">
          ${processedAdvice}
        </div>
      `
    } else {
      contentToShow = `
        <div class="blood-glucose-analysis ai-analysis-content">
          ${processedAdvice}
        </div>
      `
    }
    
    // ! 移除 ElMessageBox.alert，改为显示自定义模态框
    fullAnalysisContent.value = contentToShow
    showFullAnalysisCard.value = true
    
  } catch (error) {
    console.error('获取血糖风险评估失败:', error)
    ElMessage.error('获取血糖风险评估失败，请稍后再试')
    
    // 错误时回退到本地静态建议，并显示在新的模态框中
    const staticAdvice = `
      <h3>血糖管理建议</h3>
      <p>很抱歉，无法获取实时血糖分析。以下是基于通用规则的建议：</p>
      
      <h4>血糖管理原则</h4>
      <ul>
        <li>保持规律饮食，避免暴饮暴食</li>
        <li>增加体育活动，每天至少30分钟中等强度运动</li>
        <li>按时服药，遵医嘱调整药物剂量</li>
        <li>定期监测血糖，记录变化趋势</li>
        <li>避免过度疲劳和精神压力</li>
      </ul>
      
      <h4>监测提示</h4>
      <p>建议继续监测并记录您的血糖值，特别是在餐前和餐后2小时的数值，这将有助于更准确地评估您的血糖控制情况。</p>
    `
    
    fullAnalysisContent.value = `<div class="blood-glucose-analysis ai-analysis-content">${staticAdvice}</div>`
    showFullAnalysisCard.value = true
  }
}

// 同步设备数据
const syncDevice = async () => {
  try {
    ElMessage.info('开始同步设备数据...')
    
    // 直接刷新血糖数据，不调用不存在的同步API
    const result = await fetchGlucoseData()
    
    if (result && result.success) {
      ElMessage.success('设备数据同步成功')
      
      // 分析血糖数据
      await analyzeGlucoseData()
      
      // 获取三天分析
      await fetchGlucoseAnalysis()
      
      // 重新初始化图表
      if (hasGlucoseData.value) {
        chartKey.value++ // 强制重新渲染
        await nextTick()
        initGlucoseChart()
      }
    } else {
      ElMessage.warning('设备数据同步失败')
    }
  } catch (error) {
    console.error('同步设备数据失败:', error)
    ElMessage.error('同步设备数据失败，请检查设备连接')
  }
}
</script>

<style scoped>
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 定义主题色变量 */
:root {
  --metric-color: #2ecc71; /* 绿色 */
  --diet-suggestion-color: #e67e22; /* 橙色 */
  --diet-record-color: #f1c40f; /* 黄色 */
  --glucose-monitor-color: #3498db; /* 蓝色 */
  --reminder-color: #9b59b6; /* 紫色 */
  --knowledge-color: #34495e; /* 深蓝灰色 */
}

.dashboard-container {
  padding: 24px;
  background-color: #f0f4f8;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.el-card {
  margin-bottom: 24px;
  border-radius: 16px;
  border: none;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden; /* 配合圆角 */
  animation: fadeInUp 0.5s ease-in-out forwards;
  opacity: 0; /* 初始状态为透明 */
}

/* 为不同的卡片添加动画延迟，实现错落效果 */
.el-row > .el-col:nth-child(1) .el-card { animation-delay: 0.1s; }
.el-row > .el-col:nth-child(2) .el-card { animation-delay: 0.2s; }
.el-row > .el-col:nth-child(3) .el-card { animation-delay: 0.3s; }
.el-row .el-col .el-row > .el-col:nth-child(1) .el-card { animation-delay: 0.2s; }
.el-row .el-col .el-row > .el-col:nth-child(2) .el-card { animation-delay: 0.3s; }
.el-row .el-col .el-row > .el-col:nth-child(3) .el-card { animation-delay: 0.4s; }

.el-card:hover {
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 1.1rem;
  color: #2c3e50;
  border-bottom: 1px solid #eef2f7;
  padding-bottom: 10px;
}

/* 为特定卡片添加彩色左边框 */
.metric-card { border-left: 5px solid var(--metric-color); }
.diet-suggestion-card { border-left: 5px solid var(--diet-suggestion-color); }
.diet-card { border-left: 5px solid var(--diet-record-color); }
.glucose-card { border-left: 5px solid var(--glucose-monitor-color); }
.reminder-card { border-left: 5px solid var(--reminder-color); }
.knowledge-card { border-left: 5px solid var(--knowledge-color); }

/* 为卡片头部的文字或图标应用主题色 */
.metric-card .card-header span { color: var(--metric-color); }
.diet-suggestion-card .card-header span { color: var(--diet-suggestion-color); }
.diet-card .card-header span { color: var(--diet-record-color); }
.glucose-card .card-header span { color: var(--glucose-monitor-color); }
.reminder-card .card-header span { color: var(--reminder-color); }
.knowledge-card .card-header span { color: var(--knowledge-color); }

.welcome-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-text {
  /* The container no longer needs special styling for the effect */
}

.welcome-text h2 {
  font-size: 2.2rem;
  font-weight: 300;
  margin: 0 0 8px 0;
  color: transparent;
  background: linear-gradient(90deg, #d2d2d2, #ffffff, #d2d2d2);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  animation: text-shine 4s linear infinite;
}

.welcome-text p {
  font-size: 1rem;
  opacity: 0.9;
  margin: 0;
}

@keyframes text-shine {
  to {
    background-position: -200% center;
  }
}

.welcome-actions {
  display: flex;
  gap: 16px;
}

.welcome-actions .button {
  --white: #ffe7ff;
  --purple-100: #f4b1fd;
  --purple-200: #d190ff;
  --purple-300: #c389f2;
  --purple-400: #8e26e2;
  --purple-500: #5e2b83;
  --radius: 12px;

  border-radius: var(--radius);
  outline: none;
  cursor: pointer;
  font-size: 20px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background: transparent;
  letter-spacing: -1px;
  border: 0;
  position: relative;
  width: 160px;
  height: 60px;
  transform: rotate(353deg) skewX(4deg);
}

.welcome-actions .bg {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  filter: blur(1px);
}
.welcome-actions .bg::before,
.welcome-actions .bg::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: calc(var(--radius) * 1.1);
  background: var(--purple-500);
}
.welcome-actions .bg::before {
  filter: blur(5px);
  transition: all 0.3s ease;
  box-shadow:
    -7px 6px 0 0 rgb(115 75 155 / 40%),
    -14px 12px 0 0 rgb(115 75 155 / 30%),
    -21px 18px 4px 0 rgb(115 75 155 / 25%),
    -28px 24px 8px 0 rgb(115 75 155 / 15%),
    -35px 30px 12px 0 rgb(115 75 155 / 12%),
    -42px 36px 16px 0 rgb(115 75 155 / 8%),
    -56px 42px 20px 0 rgb(115 75 155 / 5%);
}

.welcome-actions .wrap {
  border-radius: inherit;
  overflow: hidden;
  height: 100%;
  transform: translate(6px, -6px);
  padding: 3px;
  background: linear-gradient(
    to bottom,
    var(--purple-100) 0%,
    var(--purple-400) 100%
  );
  position: relative;
  transition: all 0.3s ease;
}

.welcome-actions .outline {
  position: absolute;
  overflow: hidden;
  inset: 0;
  opacity: 0;
  outline: none;
  border-radius: inherit;
  transition: all 0.4s ease;
}
.welcome-actions .outline::before {
  content: "";
  position: absolute;
  inset: 2px;
  width: 120px;
  height: 300px;
  margin: auto;
  background: linear-gradient(
    to right,
    transparent 0%,
    white 50%,
    transparent 100%
  );
  animation: spin 3s linear infinite;
  animation-play-state: paused;
}

.welcome-actions .content {
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  position: relative;
  height: 100%;
  gap: 16px;
  border-radius: calc(var(--radius) * 0.85);
  font-weight: 600;
  transition: all 0.3s ease;
  background: linear-gradient(
    to bottom,
    var(--purple-300) 0%,
    var(--purple-400) 100%
  );
  box-shadow:
    inset -2px 12px 11px -5px var(--purple-200),
    inset 1px -3px 11px 0px rgb(0 0 0 / 35%);
}
.welcome-actions .content::before {
  content: "";
  inset: 0;
  position: absolute;
  z-index: 10;
  width: 80%;
  top: 45%;
  bottom: 35%;
  opacity: 0.7;
  margin: auto;
  background: linear-gradient(to bottom, transparent, var(--purple-400));
  filter: brightness(1.3) blur(5px);
}

.welcome-actions .char {
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.welcome-actions .char span {
  display: block;
  color: transparent;
  position: relative;
}
.welcome-actions .char span:nth-child(5) {
  margin-left: 5px;
}
.welcome-actions .char.state-1 span:nth-child(5) {
  margin-right: -3px;
}
.welcome-actions .char.state-1 span {
  animation: charAppear 1.2s ease backwards calc(var(--i) * 0.03s);
}
.welcome-actions .char.state-1 span::before,
.welcome-actions .char span::after {
  content: attr(data-label);
  position: absolute;
  color: var(--white);
  text-shadow: -1px 1px 2px var(--purple-500);
  left: 0;
}
.welcome-actions .char span::before {
  opacity: 0;
  transform: translateY(-100%);
}
.welcome-actions .char.state-2 {
  position: absolute;
  left: 80px;
}
.welcome-actions .char.state-2 span::after {
  opacity: 1;
}

.welcome-actions .icon {
  animation: resetArrow 0.8s cubic-bezier(0.7, -0.5, 0.3, 1.2) forwards;
  z-index: 10;
}
.welcome-actions .icon div,
.welcome-actions .icon div::before,
.welcome-actions .icon div::after {
  height: 3px;
  border-radius: 1px;
  background-color: var(--white);
}
.welcome-actions .icon div::before,
.welcome-actions .icon div::after {
  content: "";
  position: absolute;
  right: 0;
  transform-origin: center right;
  width: 14px;
  border-radius: 15px;
  transition: all 0.3s ease;
}
.welcome-actions .icon div {
  position: relative;
  width: 24px;
  box-shadow: -2px 2px 5px var(--purple-400);
  transform: scale(0.9);
  background: linear-gradient(to bottom, var(--white), var(--purple-100));
  animation: swingArrow 1s ease-in-out infinite;
  animation-play-state: paused;
}
.welcome-actions .icon div::before {
  transform: rotate(44deg);
  top: 1px;
  box-shadow: 1px -2px 3px -1px var(--purple-400);
  animation: rotateArrowLine 1s linear infinite;
  animation-play-state: paused;
}
.welcome-actions .icon div::after {
  bottom: 1px;
  transform: rotate(316deg);
  box-shadow: -2px 2px 3px 0 var(--purple-400);
  background: linear-gradient(200deg, var(--white), var(--purple-100));
  animation: rotateArrowLine2 1s linear infinite;
  animation-play-state: paused;
}

.welcome-actions .path {
  position: absolute;
  z-index: 12;
  bottom: 0;
  left: 0;
  right: 0;
  stroke-dasharray: 150 480;
  stroke-dashoffset: 150;
  pointer-events: none;
}

.welcome-actions .splash {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  stroke-dasharray: 60 60;
  stroke-dashoffset: 60;
  transform: translate(-17%, -31%);
  stroke: var(--purple-300);
}

/** STATES */

.welcome-actions .button:hover .words {
  opacity: 1;
}
.welcome-actions .button:hover .words span {
  animation-play-state: running;
}

.welcome-actions .button:hover .char.state-1 span::before {
  animation: charAppear 0.7s ease calc(var(--i) * 0.03s);
}

.welcome-actions .button:hover .char.state-1 span::after {
  opacity: 1;
  animation: charDisappear 0.7s ease calc(var(--i) * 0.03s);
}

.welcome-actions .button:hover .wrap {
  transform: translate(8px, -8px);
}

.welcome-actions .button:hover .outline {
  opacity: 1;
}

.welcome-actions .button:hover .outline::before,
.welcome-actions .button:hover .icon div::before,
.welcome-actions .button:hover .icon div::after,
.welcome-actions .button:hover .icon div {
  animation-play-state: running;
}

.welcome-actions .button:active .bg::before {
  filter: blur(5px);
  opacity: 0.7;
  box-shadow:
    -7px 6px 0 0 rgb(115 75 155 / 40%),
    -14px 12px 0 0 rgb(115 75 155 / 25%),
    -21px 18px 4px 0 rgb(115 75 155 / 15%);
}
.welcome-actions .button:active .content {
  box-shadow:
    inset -1px 12px 8px -5px rgba(71, 0, 137, 0.4),
    inset 0px -3px 8px 0px var(--purple-200);
}

.welcome-actions .button:active .words,
.welcome-actions .button:active .outline {
  opacity: 0;
}

.welcome-actions .button:active .wrap {
  transform: translate(3px, -3px);
}

.welcome-actions .button:active .splash {
  animation: splash 0.8s cubic-bezier(0.3, 0, 0, 1) forwards 0.05s;
}

.welcome-actions .button:focus .path {
  animation: path 1.6s ease forwards 0.2s;
}

.welcome-actions .button:focus .icon {
  animation: arrow 1s cubic-bezier(0.7, -0.5, 0.3, 1.5) forwards;
}

.welcome-actions .char.state-2 span::after,
.welcome-actions .button:focus .char.state-1 span {
  animation: charDisappear 0.5s ease forwards calc(var(--i) * 0.03s);
}

.welcome-actions .button:focus .char.state-2 span::after {
  animation: charAppear 1s ease backwards calc(var(--i) * 0.03s);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes charAppear {
  0% {
    transform: translateY(50%);
    opacity: 0;
    filter: blur(20px);
  }
  20% {
    transform: translateY(70%);
    opacity: 1;
  }
  50% {
    transform: translateY(-15%);
    opacity: 1;
    filter: blur(0);
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes charDisappear {
  0% {
    transform: translateY(0);
    opacity: 1;
  }
  100% {
    transform: translateY(-70%);
    opacity: 0;
    filter: blur(3px);
  }
}

@keyframes arrow {
  0% {
    opacity: 1;
  }
  50% {
    transform: translateX(60px);
    opacity: 0;
  }
  51% {
    transform: translateX(-200px);
    opacity: 0;
  }
  100% {
    transform: translateX(-128px);
    opacity: 1;
  }
}

@keyframes swingArrow {
  50% {
    transform: translateX(5px) scale(0.9);
  }
}

@keyframes rotateArrowLine {
  50% {
    transform: rotate(30deg);
  }
  80% {
    transform: rotate(55deg);
  }
}

@keyframes rotateArrowLine2 {
  50% {
    transform: rotate(330deg);
  }
  80% {
    transform: rotate(300deg);
  }
}

@keyframes resetArrow {
  0% {
    transform: translateX(-128px);
  }
  100% {
    transform: translateX(0);
  }
}

@keyframes path {
  from {
    stroke: white;
  }
  to {
    stroke-dashoffset: -480;
    stroke: #f9c6fe;
  }
}

@keyframes splash {
  to {
    stroke-dasharray: 2 60;
    stroke-dashoffset: -60;
  }
}

.chart-card {
  display: flex;
  flex-direction: column;
  height: 420px; /* 增加一些高度 */
  padding: 0;
  animation: fadeInUp 0.5s ease-in-out forwards;
  opacity: 0;
  animation-delay: 0.2s; /* 延迟动画 */
}

.chart-card .el-card__header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-card .el-card__body {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 关键修复：允许flex子项收缩 */
}

.chart-container {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.chart {
  width: 100%;
  height: 100%;
}

.metrics-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 12px;
}

.metric-label {
  color: #576b81;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--metric-color);
}

.diet-card .diet-list {
  padding: 0 10px;
}

.diet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eef2f7;
}

.diet-item:last-child {
  border-bottom: none;
}

.diet-time {
  font-size: 0.9rem;
  color: #576b81;
  width: 30%;
  font-weight: 500;
}

.diet-name {
  flex: 1;
  font-weight: 500;
}

.diet-calories {
  color: var(--diet-record-color);
  font-weight: 600;
}

.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reminder-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 10px;
  transition: background-color 0.3s;
}

.reminder-icon {
  margin-right: 12px;
  font-size: 1.4rem;
  color: var(--reminder-color);
}

.reminder-icon.done {
  color: #2ecc71;
}

.reminder-content {
  flex: 1;
}

.reminder-text {
  font-weight: 600;
  color: #2c3e50;
}

.reminder-time {
  font-size: 0.8rem;
  color: #576b81;
}

.reminder-item .el-checkbox {
  margin-left: 10px;
}

.knowledge-item {
  padding: 16px 0;
  border-bottom: 1px solid #eef2f7;
}

.knowledge-item:last-child {
  border-bottom: none;
}

.knowledge-title {
  font-weight: 600;
  margin-bottom: 6px;
  color: #2c3e50;
}

.knowledge-desc {
  font-size: 0.9rem;
  color: #576b81;
  margin-bottom: 12px;
}

.knowledge-item .el-button {
  font-weight: 600;
}

.card-footer {
  margin-top: 16px;
  text-align: center;
}

.empty-data {
  padding: 40px 0;
}

.loading-container {
  padding: 20px;
}

.glucose-card .card-header {
  border-bottom: none;
}

.quick-import {
  padding: 10px 5px;
}

.quick-import h4 {
  margin-bottom: 15px;
  color: var(--glucose-monitor-color);
  font-weight: 600;
}

.quick-import .el-button {
  border-radius: 8px;
  font-weight: 600;
}

.glucose-alerts {
  margin-bottom: 15px;
}

.glucose-alerts .el-alert {
  margin-bottom: 10px;
  border-radius: 8px;
}

.glucose-alerts .el-alert:last-child {
  margin-bottom: 0;
}

/* 智能分析相关样式 */
.glucose-analysis {
  margin-top: 10px;
}

.analysis-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.summary-item {
  text-align: center;
  flex: 1;
  padding: 12px 0;
  border-radius: 12px;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 13px;
  font-weight: 500;
}

.normal-value { background-color: rgba(46, 204, 113, 0.1); color: #2ecc71; }
.high-value { background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; }
.low-value { background-color: rgba(243, 156, 18, 0.1); color: #f39c12; }

.good-range { background-color: rgba(46, 204, 113, 0.1); color: #2ecc71; }
.average-range { background-color: rgba(243, 156, 18, 0.1); color: #f39c12; }
.poor-range { background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; }

.stable-std { background-color: rgba(46, 204, 113, 0.1); color: #2ecc71; }
.moderate-std { background-color: rgba(243, 156, 18, 0.1); color: #f39c12; }
.unstable-std { background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; }

.advice-preview {
  background-color: #eaf5ff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 10px;
  border: 1px solid #a8d8ff;
}

.advice-title {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: var(--glucose-monitor-color);
  font-weight: 600;
}

.advice-title .el-icon {
  margin-right: 8px;
  font-size: 1.2rem;
}

.advice-content {
  font-size: 14px;
  line-height: 1.6;
  color: #34495e;
  margin-bottom: 8px;
}

.empty-analysis {
  padding: 15px 0;
  text-align: center;
}

/* 对话框样式 */
:deep(.advice-dialog .el-message-box__content) {
  max-height: 400px;
  overflow-y: auto;
}

.diet-suggestion-card .card-header {
  border-bottom: none;
}

.diet-status-banner {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 15px;
  font-size: 14px;
  font-weight: 600;
}

.diet-status-banner .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.status-normal {
  background-color: rgba(46, 204, 113, 0.15);
  color: #27ae60;
  border-left: 5px solid #2ecc71;
}

.status-high {
  background-color: rgba(231, 76, 60, 0.15);
  color: #c0392b;
  border-left: 5px solid #e74c3c;
}

.status-low {
  background-color: rgba(243, 156, 18, 0.15);
  color: #d35400;
  border-left: 5px solid #f39c12;
}

.diet-suggestion-content {
  padding: 0 5px;
}

.suggestion-text {
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
  color: #34495e;
}

.food-section {
  margin-bottom: 20px;
}

.food-section h4 {
  font-size: 15px;
  margin-bottom: 10px;
  color: #2c3e50;
  font-weight: 600;
}

.food-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.food-tag {
  border-radius: 16px;
  padding: 0 15px;
  height: 32px;
  line-height: 30px;
  font-weight: 500;
}

.next-meal {
  margin: 20px 0;
}

.meal-type-selector {
  margin-bottom: 15px;
  text-align: center;
}

.meal-suggestion {
  background-color: #f0f4f8;
  padding: 15px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: #34495e;
  text-align: center;
  border: 1px dashed #bdc3c7;
}

.card-footer {
  margin-top: 20px;
  text-align: center;
}

:deep(.diet-suggestion-dialog .el-message-box__content) {
  max-height: 400px;
  overflow-y: auto;
}

:deep(.diet-suggestion-dialog ul) {
  padding-left: 20px;
  margin: 10px 0;
  list-style-type: "✨ ";
}

:deep(.diet-suggestion-dialog h3, .diet-suggestion-dialog h4) {
  margin: 15px 0 10px 0;
  color: #0072ff;
}

:deep(.diet-suggestion-dialog .blood-glucose-analysis) {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

:deep(.diet-suggestion-dialog .additional-meal-suggestions) {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
}

:deep(.diet-suggestion-dialog strong) {
  color: #303133;
}

@media (max-width: 992px) {
  .metrics-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 15px;
  }
  .welcome-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .metrics-container, .analysis-summary {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 576px) {
  .metrics-container, .analysis-summary {
    grid-template-columns: 1fr;
  }
  .welcome-text h2 {
    font-size: 1.8rem;
  }
  .welcome-actions {
    flex-direction: column;
    width: 100%;
  }
}

/* 添加AI血糖风险评估容器样式 */
.ai-alert-container {
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 15px;
  border: 1px solid;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease-in-out;
}

.ai-alert-good {
  background-color: #f0f9eb;
  border-color: #e1f3d8;
}

.ai-alert-warning {
  background-color: #fdf6ec;
  border-color: #faecd8;
}

.ai-alert-danger {
  background-color: #fff6f6;
  border-color: #ffd6d6;
}

.ai-alert-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
}

.ai-alert-good .ai-alert-header { color: #67c23a; }
.ai-alert-warning .ai-alert-header { color: #e6a23c; }
.ai-alert-danger .ai-alert-header { color: #f56c6c; }

.ai-alert-header .el-icon {
  margin-right: 8px;
  font-size: 1.2rem;
}

.ai-alert-content {
  font-size: 14px;
  line-height: 1.6;
  color: #34495e;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #fff;
  border-radius: 8px;
  border-left: 3px solid;
}

.ai-alert-good .ai-alert-content { border-left-color: #67c23a; }
.ai-alert-warning .ai-alert-content { border-left-color: #e6a23c; }
.ai-alert-danger .ai-alert-content { border-left-color: #f56c6c; }

/* 对话框中AI分析内容的样式 */
:deep(.advice-dialog .ai-analysis-content) {
  line-height: 1.6;
  font-size: 14px;
}

:deep(.advice-dialog .ai-analysis-content h3) {
  color: #e74c3c;
  margin: 16px 0 8px 0;
  font-size: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}

:deep(.advice-dialog .ai-analysis-content h4) {
  color: #2c3e50;
  margin: 14px 0 8px 0;
  font-size: 15px;
}

:deep(.advice-dialog .ai-analysis-content strong) {
  color: #e74c3c;
  font-weight: 600;
}

:deep(.advice-dialog .el-message-box__content) {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
}

:deep(.advice-dialog .el-message-box__header) {
  background-color: #f8f9fb;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

/* 新增：血糖预警消息样式 */
:deep(.glucose-alert-warning) {
  background-color: #fff6f6;
  border: 1px solid #ffd6d6;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

:deep(.glucose-alert-warning h3) {
  color: #e74c3c;
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  display: flex;
  align-items: center;
}

:deep(.glucose-alert-warning p) {
  color: #333;
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}

/* 详细建议卡片的动画延迟 */
.detailed-advice-card {
  animation-delay: 0s;
}

.el-card:hover {
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  border-left: 5px solid var(--knowledge-color);
}

.advice-content-wrapper {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 15px; /* for scrollbar */
}

.advice-content-wrapper h3, .advice-content-wrapper h4 {
  margin: 15px 0 10px 0;
  color: #0072ff;
}
.advice-content-wrapper .blood-glucose-analysis {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}
.advice-content-wrapper .additional-meal-suggestions {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
}
.advice-content-wrapper strong {
  color: #303133;
}
.advice-content-wrapper ul {
  padding-left: 20px;
  margin: 10px 0;
  list-style-type: "✨ ";
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-card {
  width: 90%;
  max-width: 800px;
  margin: 0;
  opacity: 0;
  transform: scale(0.9);
  animation: modal-pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

@keyframes modal-pop-in {
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 新增：完整分析卡片的样式 */
.full-analysis-card {
}

.el-card:hover {
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  border-left: 5px solid var(--knowledge-color);
}

.advice-content-wrapper {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
}

.advice-content-wrapper h3, .advice-content-wrapper h4 {
  margin: 15px 0 10px 0;
  color: #0072ff;
}

.advice-content-wrapper .blood-glucose-analysis {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

.advice-content-wrapper .additional-meal-suggestions {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
}

.advice-content-wrapper strong {
  color: #303133;
}

.advice-content-wrapper ul {
  padding-left: 20px;
  margin: 10px 0;
  list-style-type: "✨ ";
}

/* 模态卡片头部的通用样式 */
.modal-card .card-header {
  background-color: #f8f9fb;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

/* 新增欢迎卡片加载器样式 */
.welcome-loader-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 160px; /* 确保加载器有足够的空间显示 */
}

.loader {
  position: relative;
  width: 240px;
  height: 130px;
  margin-bottom: 10px;
  border: 1px solid #d3d3d3;
  padding: 15px;
  background-color: #e3e3e3;
  overflow: hidden;
}

.loader:after {
  content: "";
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: linear-gradient(110deg, rgba(227, 227, 227, 0) 0%, rgba(227, 227, 227, 0) 40%, rgba(227, 227, 227, 0.5) 50%, rgba(227, 227, 227, 0) 60%, rgba(227, 227, 227, 0) 100%);
  animation: gradient-animation_2 1.2s linear infinite;
}

.loader .wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.loader .wrapper > div {
  background-color: #cacaca;
}

.loader .circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

.loader .button {
  display: inline-block;
  height: 32px;
  width: 75px;
}

.loader .line-1 {
  position: absolute;
  top: 11px;
  left: 58px;
  height: 10px;
  width: 100px;
}

.loader .line-2 {
  position: absolute;
  top: 34px;
  left: 58px;
  height: 10px;
  width: 150px;
}

.loader .line-3 {
  position: absolute;
  top: 57px;
  left: 0px;
  height: 10px;
  width: 100%;
}

.loader .line-4 {
  position: absolute;
  top: 80px;
  left: 0px;
  height: 10px;
  width: 92%;
}

@keyframes gradient-animation_2 {
  0% {
    transform: translateX(-100%);
  }

  100% {
    transform: translateX(100%);
  }
}

.diet-loader-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px; /* Ensure enough space for the animation */
}

/* Pizza animation CSS from uiverse.io/AkshatDaxini/jolly-hound-16 */
.main {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  border-radius: 12px; /* Match card border-radius */
}

#pizza {
  animation: rotate 4s linear infinite; /* Rotate the entire pizza */
  transform-origin: 82px 79.5px; /* Center of the pizza */
}

#slice6 {
  animation: slice6 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice5 {
  animation: slice5 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice4 {
  animation: slice4 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice3 {
  animation: slice3 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice2 {
  animation: slice2 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice1 {
  animation: slice1 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}

#pepperoni {
  animation: pepperoni 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_2 {
  animation: pepperoni_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_3 {
  animation: pepperoni_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_4 {
  animation: pepperoni_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_5 {
  animation: pepperoni_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_6 {
  animation: pepperoni_6 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

#mushroom {
  animation: mushroom 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_2 {
  animation: mushroom_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_3 {
  animation: mushroom_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_4 {
  animation: mushroom_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_5 {
  animation: mushroom_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

#onion {
  animation: onion 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_2 {
  animation: onion_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_3 {
  animation: onion_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_4 {
  animation: onion_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_5 {
  animation: onion_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_6 {
  animation: onion_6 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

#pepper {
  animation: pepper 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_2 {
  animation: pepper_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_3 {
  animation: pepper_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_4 {
  animation: pepper_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_5 {
  animation: pepper_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_6 {
  animation: pepper_6 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes slice6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(5px, -5px);
  }
}

@keyframes slice5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(5px, 5px);
  }
}

@keyframes slice4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-5px, 5px);
  }
}

@keyframes slice3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-5px, -5px);
  }
}

@keyframes slice2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, 5px);
  }
}

@keyframes slice1 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, -5px);
  }
}

@keyframes pepperoni {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-2px, -2px);
  }
}
@keyframes pepperoni_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(2px, -2px);
  }
}
@keyframes pepperoni_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-2px, 2px);
  }
}
@keyframes pepperoni_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(2px, 2px);
  }
}
@keyframes pepperoni_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-2px, 0);
  }
}
@keyframes pepperoni_6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(2px, 0);
  }
}

@keyframes mushroom {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1px, -1px);
  }
}
@keyframes mushroom_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1px, -1px);
  }
}
@keyframes mushroom_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1px, 1px);
  }
}
@keyframes mushroom_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1px, 1px);
  }
}
@keyframes mushroom_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, -1px);
  }
}

@keyframes onion {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-0.5px, -0.5px);
  }
}
@keyframes onion_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0.5px, -0.5px);
  }
}
@keyframes onion_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-0.5px, 0.5px);
  }
}
@keyframes onion_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0.5px, 0.5px);
  }
}
@keyframes onion_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, -0.5px);
  }
}
@keyframes onion_6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, 0.5px);
  }
}

@keyframes pepper {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1.5px, -1.5px);
  }
}
@keyframes pepper_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.5px, -1.5px);
  }
}
@keyframes pepper_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1.5px, 1.5px);
  }
}
@keyframes pepper_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.5px, 1.5px);
  }
}
@keyframes pepper_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1.5px, 0);
  }
}
@keyframes pepper_6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.5px, 0);
  }
}

/* Water Wave Effect Styles */
.e-card {
  margin: 100px auto;
  background: transparent;
  box-shadow: 0px 8px 28px -9px rgba(0,0,0,0.45);
  position: relative;
  width: 240px;
  height: 330px;
  border-radius: 16px;
  overflow: hidden;
}

.wave {
  position: absolute;
  width: 540px;
  height: 700px;
  opacity: 0.6;
  left: 0;
  top: 0;
  margin-left: -50%;
  margin-top: -70%;
  background: linear-gradient(744deg,#af40ff,#5b42f3 60%,#00ddeb);
}

.icon {
  width: 3em;
  margin-top: -1em;
  padding-bottom: 1em;
}

.infotop {
  text-align: center;
  font-size: 20px;
  position: absolute;
  top: 5.6em;
  left: 0;
  right: 0;
  color: rgb(255, 255, 255);
  font-weight: 600;
}

.name {
  font-size: 14px;
  font-weight: 100;
  position: relative;
  top: 1em;
  text-transform: lowercase;
}

.wave:nth-child(2),
.wave:nth-child(3) {
  top: 210px;
}

.playing .wave {
  border-radius: 40%;
  animation: wave 3000ms infinite linear;
}

.wave {
  border-radius: 40%;
  animation: wave 55s infinite linear;
}

.playing .wave:nth-child(2) {
  animation-duration: 4000ms;
}

.wave:nth-child(2) {
  animation-duration: 50s;
}

.playing .wave:nth-child(3) {
  animation-duration: 5000ms;
}

.wave:nth-child(3) {
  animation-duration: 45s;
}

@keyframes wave {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

/* 为所有卡片（除了欢迎卡片）添加通用样式和悬停效果 */
.el-card:not(.welcome-card) {
  border-radius: 16px;
  border: 1px solid #e5e5e5; /* 添加一个浅色边框来定义边缘 */
  box-shadow: 0px 5px 0px 0px #e0e0e0; /* 使用无模糊的阴影创建厚度感 */
  transition: all 0.2s ease-in-out;
  position: relative; /* 为悬停时的位置调整做准备 */
  top: 0;
}

.el-card:not(.welcome-card):hover {
  top: -5px; /* 向上移动卡片，产生按下的感觉 */
  box-shadow: 0px 10px 0px 0px #d1d1d1; /* 悬停时增加厚度感 */
  transform: translateY(-5px) scale(1.02); /* 保留原有的上浮和放大效果 */
}

.el-row {
  width: 100%;
}

</style>
