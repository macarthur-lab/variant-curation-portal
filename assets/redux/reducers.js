import { actionTypes } from "./actions";

/* eslint-disable import/prefer-default-export */
export const curationResultReducer = (state, action) => {
  if (state === undefined) {
    return {
      value: null,
      errors: null,
    };
  }

  switch (action.type) {
    case actionTypes.SET_RESULT:
      if (action.reset) {
        return {
          errors: null,
          value: action.result,
        };
      }
      return {
        ...state,
        value: action.result,
      };
    case actionTypes.SET_RESULT_ERRORS:
      return {
        ...state,
        errors: action.errors,
      };
    default:
      return state;
  }
};
