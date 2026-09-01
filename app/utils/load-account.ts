// The two reads every signed-in session starts with. Both collapse into a
// single request each, so calling this twice is free — which is what lets app
// boot and sign-in share it without either knowing about the other.
export function loadAccount() {
  return Promise.all([useFeedsStore().load(), useSettingsStore().load()])
}
