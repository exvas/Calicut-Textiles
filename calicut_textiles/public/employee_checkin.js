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

    // Calculate shift start time based on "start" object (with hours & minutes)
    const shift_start_today = moment(frm.doc.time).startOf('day')
        .add(start.hours(), 'hours')
        .add(start.minutes(), 'minutes');

    // Add 10 minutes grace period
    const grace_end_time = shift_start_today.clone().add(10, 'minutes');

    let late_minutes = 0;
    if (checkin_time.isAfter(grace_end_time)) {
        late_minutes = checkin_time.diff(grace_end_time, 'minutes');
    }

    frm.set_value('custom_late_coming_minutes', late_minutes);
}


function calculate_early_going(frm, end) {
    const checkout_time = moment(frm.doc.time);

    // Calculate today's shift end time from the 'end' object
    const shift_end_today = moment(frm.doc.time).startOf('day')
        .add(end.hours(), 'hours')
        .add(end.minutes(), 'minutes');

    // Grace period ends 10 minutes *before* shift end
    const grace_start_time = shift_end_today.clone().subtract(10, 'minutes');

    let early_minutes = 0;

    // If checkout is before the grace start time, calculate early minutes
    if (checkout_time.isBefore(grace_start_time)) {
        early_minutes = grace_start_time.diff(checkout_time, 'minutes');
    }

    console.log("Checkout Time:", checkout_time.format());
    console.log("Shift End Time:", shift_end_today.format());
    console.log("Grace Start Time:", grace_start_time.format());
    console.log("Early Going Minutes:", early_minutes);

    frm.set_value('custom_early_going_minutes', early_minutes);
}
