/** Cổng công khai của entity `dish`. Tầng trên chỉ được import từ đây. */
export { DishCard } from './ui/DishCard';
export { useDishImages } from './model/useDishImages';
export type { AnhMon } from './model/useDishImages';
export {
  describeCookingMethod,
  describeIntroState,
  describeMealTimes,
  describeRestaurantCount,
  describeSource,
  describeSpice,
  describeTemperature,
} from './model/format';
