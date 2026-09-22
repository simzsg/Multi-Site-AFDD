export const example =
  "For all office properties, monitor AHUs serving tenant areas. While an AHU is ON, if supply-air temperature differs from its setpoint by more than 3°C continuously for 15 minutes, create a Critical issue.";
export const date = (value?: string | null) =>
  value
    ? new Date(value).toLocaleString([], {
        timeZone: "UTC",
        timeZoneName: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "Not yet observed";
export const time = (value: string) =>
  new Date(value).toLocaleTimeString([], {
    timeZone: "UTC",
    timeZoneName: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
export const stale = (value?: string, age = 120) =>
  !value || Date.now() - new Date(value).getTime() > age * 1000;
