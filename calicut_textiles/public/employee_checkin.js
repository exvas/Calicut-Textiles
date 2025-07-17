frappe.ui.form.on('Employee Checkin', {
    employee: function(frm) {
        if (frm.is_new() && frm.doc.employee) {
            frappe.db.get_value('Employee', frm.doc.employee, 'default_shift', (employeeData) => {
                if (employeeData && employeeData.default_shift) {
                    let shift_type = employeeData.default_shift;

                    frappe.db.get_doc('Shift Type', shift_type).then(shiftDoc => {
                        if (shiftDoc.start_time && shiftDoc.end_time) {
                            const start = moment(shiftDoc.start_time, 'HH:mm:ss');
                            const end = moment(shiftDoc.end_time, 'HH:mm:ss');

                            frm.shift_start = start;
                            frm.shift_end = end;

                            let duration = moment.duration(end.diff(start));
                            if (duration.asMinutes() < 0) {
                                duration = moment.duration(end.add(1, 'day').diff(start));
                            }

                            const hours = Math.floor(duration.asHours());
                            const minutes = duration.minutes();
                            const total_hours = `${hours}.${minutes.toString().padStart(2, '0')}`;
                            frm.set_value('custom_total_hours', total_hours);

                            if (frm.doc.time) {
                              frappe.call({
                                  method: "frappe.client.get_list",
                                  args: {
                                      doctype: "Employee Checkin",
                                      filters: {
                                          employee: frm.doc.employee,
                                          time: ["between", [
                                              frappe.datetime.get_today() + " 00:00:00",
                                              frappe.datetime.get_today() + " 23:59:59"
                                          ]]
                                      },
                                      fields: ["name", "time"],
                                      order_by: "time asc",
                                      limit_page_length: 100
                                  },
                                  callback: function(r) {
                                      if (r.message && r.message.length > 0) {
                                          let logs = r.message;
                                          let first_log = logs[0];
                                          let last_log = logs[logs.length - 1];

                                          if (frm.doc.name === first_log.name) {
                                              calculate_late_coming(frm, start);
                                          }
                                          else if (frm.doc.name === last_log.name) {
                                              calculate_early_going(frm, end);
                                          }
                                      }
                                  }
                              });
                          }

                        }
                    });
                }
            });
        }
    },

    log_type: function(frm) {
        if (!frm.doc.time || !frm.doc.employee || !frm.doc.log_type) return;

        const date = frm.doc.time.split(" ")[0];

        if (frm.doc.log_type === 'IN' && frm.shift_start) {
            calculate_late_coming(frm, frm.shift_start);
        }

        if (frm.doc.log_type === 'OUT' && frm.shift_end) {
            calculate_early_going(frm, frm.shift_end);

            frappe.call({
                method: "calicut_textiles.calicut_textiles.events.employee_checkin.get_late_minutes_from_in_log",
                args: {
                    employee: frm.doc.employee,
                    date: date
                },
                callback: function (r) {
                    if (r.message) {
                        const late = flt(r.message.custom_late_coming_minutes);
                        const early = flt(frm.doc.custom_early_going_minutes || 0);
                        frm.set_value("custom_late_coming_minutes", late);
                        frm.set_value("custom_late_early", late + early);
                    } else {
                        frm.set_value("custom_late_early", flt(frm.doc.custom_early_going_minutes || 0));
                    }
                }
            });
        }
    },

    time: function(frm) {
        if (frm.doc.log_type === 'IN' && frm.shift_start) {
            calculate_late_coming(frm, frm.shift_start);
        }
        if (frm.doc.log_type === 'OUT' && frm.shift_end) {
            calculate_early_going(frm, frm.shift_end);
        }
    }
});

function calculate_late_coming(frm, start) {
    const checkin_time = moment(frm.doc.time);
    const shift_start_today = moment(frm.doc.time).startOf('day')
        .add(start.hours(), 'hours')
        .add(start.minutes(), 'minutes');

    const diff_minutes = checkin_time.diff(shift_start_today, 'minutes');

    console.log("Check-in Time:", checkin_time.format());
    console.log("Shift Start Time:", shift_start_today.format());
    console.log("Late Minutes:", diff_minutes);

    if (diff_minutes > 10) {
        frm.set_value('custom_late_coming_minutes', diff_minutes);
    } else {
        frm.set_value('custom_late_coming_minutes', 0);
    }
}


function calculate_early_going(frm, end) {
    const checkout_time = moment(frm.doc.time);
    const shift_end_today = moment(frm.doc.time).startOf('day')
        .add(end.hours(), 'hours')
        .add(end.minutes(), 'minutes');

    const early_minutes = shift_end_today.diff(checkout_time, 'minutes');

    console.log("Check-out Time:", checkout_time.format());
    console.log("Shift End Time:", shift_end_today.format());
    console.log("Early Going Minutes:", early_minutes);

    if (early_minutes > 20) {
        frm.set_value('custom_early_going_minutes', early_minutes);
    } else {
        frm.set_value('custom_early_going_minutes', 0);
    }
}
