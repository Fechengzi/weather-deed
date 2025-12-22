Page({
  data: {
    cityName: '哈尔滨',
    tempCityName: '',
    selectedDate: '', // 格式 YYYY-MM-DD
    displayDate: '',  // 用于显示的日期
    startDate: '',    // 选择器开始时间（今天）
    endDate: '',      // 选择器结束时间（6天后）
    advice: null,
    locationTemp: null,
    items: [],
    loading: false
  },

  onLoad() {
    this.initDates();
    this.fetchAdvice(this.data.cityName, this.data.selectedDate);
  },

  // 初始化日期范围
  initDates() {
    const now = new Date();
    const today = this.formatDate(now);
    
    // 计算 6 天后的日期
    const future = new Date();
    future.setDate(now.getDate() + 6);
    const lastDay = this.formatDate(future);

    // 默认查明天
    const tomorrow = new Date();
    tomorrow.setDate(now.getDate() + 1);

    this.setData({
      startDate: today,
      endDate: lastDay,
      selectedDate: this.formatDate(tomorrow)
    });
  },

  formatDate(date) {
    const y = date.getFullYear();
    const m = (date.getMonth() + 1).toString().padStart(2, '0');
    const d = date.getDate().toString().padStart(2, '0');
    return `${y}-${m}-${d}`;
  },

// 输入框输入时触发，实时更新 tempCityName
onInputCity(e) {
  this.setData({
    tempCityName: e.detail.value
  });
},

// 点击搜索按钮触发
onSearch() {
  const targetCity = this.data.tempCityName;
  if (!targetCity) {
    wx.showToast({ title: '请输入城市名', icon: 'none' });
    return;
  }
  // 关键：将用户输入的值传进去
  this.fetchAdvice(targetCity, this.data.selectedDate);
},

// 当日期选择器发生改变时触发
onDateChange(e) {
  const newDate = e.detail.value; // 拿到用户选择的新日期
  this.setData({
    selectedDate: newDate
  });
  // 选完日期后，立即自动重新请求数据
  this.fetchAdvice(this.data.cityName, newDate);
},

fetchAdvice(city, date) {
  const that = this;
  this.setData({ loading: true });
  
  wx.request({
    url: 'http://127.0.0.1:5000/get_advice',
    data: {
      city: city, // 这里的 city 是从 onSearch 传进来的实参
      date: date
    },
    success(res) {
      if (res.statusCode === 200) {
        // 成功后，更新页面显示的城市名 cityName
        that.setData({
          cityName: res.data.city_name,
          displayDate: res.data.target_date,
          advice: res.data.advice,
          locationTemp: res.data.location_temp,
          items: res.data.advice.items,
          loading: false
        });
      }
    }
  });
}
})