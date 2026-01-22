# 动画组件库

这是一个功能完整的动画组件库，提供了两种类型的动画组件：

1. **基础动画组件** - 使用纯CSS动画，轻量级
2. **Framer Motion 动画组件** - 使用 Framer Motion 库，提供更丰富的动画效果

## 安装

```bash
npm install
```

## 运行

```bash
npm run dev
```

## 组件说明

### 1. Animate 组件（基础动画）

使用纯CSS实现的动画组件，支持多种动画类型。

**支持的动画类型：**
- `fadeIn` - 淡入
- `fadeOut` - 淡出
- `slideInUp` - 向上滑入
- `slideInDown` - 向下滑入
- `slideInLeft` - 向左滑入
- `slideInRight` - 向右滑入
- `scaleIn` - 缩放进入
- `scaleOut` - 缩放退出
- `rotate` - 旋转
- `bounce` - 弹跳
- `pulse` - 脉冲
- `shake` - 摇晃

**使用示例：**

```jsx
import Animate from './components/Animate';

<Animate type="fadeIn" duration={0.5} delay={0.1} trigger={true}>
  <div>内容</div>
</Animate>
```

**Props：**
- `type` (string) - 动画类型，默认为 'fadeIn'
- `duration` (number) - 动画持续时间（秒），默认为 0.5
- `delay` (number) - 动画延迟时间（秒），默认为 0
- `trigger` (boolean) - 触发动画的布尔值，默认为 true
- `className` (string) - 额外的CSS类名
- `children` (ReactNode) - 子元素

### 2. MotionAnimate 组件（Framer Motion）

使用 Framer Motion 实现的高级动画组件，提供更流畅的动画效果。

**支持的动画类型：**
- `fadeIn` - 淡入
- `slideUp` - 向上滑入
- `slideDown` - 向下滑入
- `slideLeft` - 向左滑入
- `slideRight` - 向右滑入
- `scale` - 缩放
- `rotate` - 旋转
- `bounce` - 弹跳

**使用示例：**

```jsx
import MotionAnimate from './components/MotionAnimate';

<MotionAnimate type="slideUp" duration={0.5} delay={0.1} trigger={true}>
  <div>内容</div>
</MotionAnimate>
```

**Props：**
- `type` (string) - 动画类型，默认为 'fadeIn'
- `duration` (number) - 动画持续时间（秒），默认为 0.5
- `delay` (number) - 动画延迟（秒），默认为 0
- `trigger` (boolean) - 是否显示，默认为 true
- `customVariants` (object) - 自定义动画变体
- `children` (ReactNode) - 子元素

### 3. MotionList 组件（列表动画）

用于为列表项添加交错动画效果。

**使用示例：**

```jsx
import { MotionList } from './components/MotionAnimate';

<MotionList stagger={0.1}>
  <div>列表项 1</div>
  <div>列表项 2</div>
  <div>列表项 3</div>
</MotionList>
```

**Props：**
- `stagger` (number) - 每个列表项之间的延迟时间（秒），默认为 0.1
- `children` (ReactNode) - 子元素

### 4. MotionHover 组件（悬停动画）

为元素添加悬停和点击动画效果。

**使用示例：**

```jsx
import { MotionHover } from './components/MotionAnimate';

<MotionHover scale={1.1}>
  <div>悬停我</div>
</MotionHover>
```

**Props：**
- `scale` (number) - 悬停时的缩放比例，默认为 1.05
- `children` (ReactNode) - 子元素

### 5. MotionDrag 组件（拖拽动画）

使元素可以拖拽，并添加拖拽动画效果。

**使用示例：**

```jsx
import { MotionDrag } from './components/MotionAnimate';

<MotionDrag>
  <div>拖拽我</div>
</MotionDrag>
```

**Props：**
- `children` (ReactNode) - 子元素

## 自定义动画

### 自定义 CSS 动画

在 `src/components/Animate.css` 中添加新的 keyframes：

```css
@keyframes myCustomAnimation {
  from {
    /* 起始状态 */
  }
  to {
    /* 结束状态 */
  }
}

.animate-myCustomAnimation {
  animation: myCustomAnimation 0.5s ease-in-out;
}
```

### 自定义 Framer Motion 动画

在 `MotionAnimate` 组件中使用 `customVariants` prop：

```jsx
const customVariants = {
  initial: { opacity: 0, x: -100 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 100 },
};

<MotionAnimate customVariants={customVariants}>
  <div>自定义动画</div>
</MotionAnimate>
```

## 最佳实践

1. **性能考虑**：对于简单的动画，使用 `Animate` 组件（CSS动画）性能更好
2. **复杂交互**：对于需要复杂交互的动画，使用 `MotionAnimate` 组件
3. **列表动画**：使用 `MotionList` 为列表添加流畅的交错动画
4. **用户交互**：使用 `MotionHover` 和 `MotionDrag` 增强用户体验

## 技术栈

- React 18
- Framer Motion 10
- Vite
- CSS3 Animations
