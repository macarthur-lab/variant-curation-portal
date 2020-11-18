import api from "../../api";

export const actionTypes = {
  SET_APP_SETTINGS: "SET_APP_SETTINGS",
};

export const loadAppSettings = () => dispatch => {
  return api.get("/settings/").then(settings => {
    dispatch({
      type: actionTypes.SET_APP_SETTINGS,
      settings,
    });
    return settings;
  });
};
