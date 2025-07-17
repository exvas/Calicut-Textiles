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

                            // Calculate total shift hours
                            let duration = moment.duration(end.diff(start));
                            if (duration.asMinutes() < 0) {
                                duration = moment.duration(end.add(1, 'day').diff(start));
                            }

                            const hours = Math.floor(duration.asHours());
                            const minutes = duration.minutes();
                            const total_hours = `${hours}.${minutes.toString().padStart(2, '0')}`;
                            frm.set_value('custom_total_hours', total_hours);

                            if (frm.doc.time) {
                              const date = frm.doc.time.split(" ")[0];

                              frappe.call({
                                  method: "calicut_textiles.calicut_textiles.events.employee_checkin.get_first_and_last_checkins",
                                  args: {
                                      employee: frm.doc.employee,
                                      date: date
                                  },
                                  callback: function (r) {
                                      if (r.message) {
                                          const current_time = moment(frm.doc.time);
                                          const first_time = r.message.first ? moment(r.message.first.time) : null;
                                          const last_time = r.message.last ? moment(r.message.last.time) : null;

                                          if (first_time && current_time.isSame(first_time)) {
                                              // Treat as IN
                                              calculate_late_coming(frm, start);
                                          }

                                          if (last_time && current_time.isSame(last_time)) {
                                              // Treat as OUT
                                              calculate_early_going(frm, end);

                                              const late = flt(r.message.first.custom_late_coming_minutes || 0);
                                              const early = flt(frm.doc.custom_early_going_minutes || 0);
                                              frm.set_value("custom_late_coming_minutes", late);
                                              frm.set_value("custom_late_early", late + early);
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

            // Fetch custom_late_coming_minutes from IN check-in of the same date
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
                        // No IN check-in found
                        frm.set_value("custom_late_early", flt(frm.doc.custom_early_going_minutes || 0));
                    }
                }
            });
        }
    },

    time: function(frm) {
        if (!frm.doc.time || !frm.doc.employee || !frm.shift_start || !frm.shift_end) return;

        const date = frm.doc.time.split(" ")[0];

        frappe.call({
            method: "calicut_textiles.calicut_textiles.events.employee_checkin.get_first_and_last_checkins",
            args: {
                employee: frm.doc.employee,
                date: date
            },
            callback: function (r) {
                if (!r.message) return;

                const current_time = moment(frm.doc.time);
                const first_time = r.message.first ? moment(r.message.first.time) : null;
                const last_time = r.message.last ? moment(r.message.last.time) : null;

                if (!first_time || !last_time) return;

                const is_first = current_time.isSame(first_time);
                const is_last = current_time.isSame(last_time);

                // Check for duplicates within 5 minutes of first or last
                const within_5_min_of_first = current_time.diff(first_time, 'minutes') <= 5 && current_time.diff(first_time, 'minutes') > 0;
                const within_5_min_of_last = last_time.diff(current_time, 'minutes') <= 5 && last_time.diff(current_time, 'minutes') > 0;

                if (is_first) {
                    // IN logic
                    calculate_late_coming(frm, frm.shift_start);
                } else if (is_last) {
                    // OUT logic
                    calculate_early_going(frm, frm.shift_end);

                    const late = flt(r.message.first.custom_late_coming_minutes || 0);
                    const early = flt(frm.doc.custom_early_going_minutes || 0);
                    frm.set_value("custom_late_coming_minutes", late);
                    frm.set_value("custom_late_early", late + early);
                } else if (within_5_min_of_first || within_5_min_of_last) {
                    // Consider duplicate
                    frappe.msgprint(__("This entry is within 5 minutes of the first or last check-in. It will be ignored for late/early calculation."));
                    frm.set_value("custom_late_coming_minutes", 0);
                    frm.set_value("custom_early_going_minutes", 0);
                    frm.set_value("custom_late_early", 0);
                } else {
                    // Entry is neither first nor last nor duplicate → ignored
                    frappe.msgprint(__("This is a middle check-in. No late/early calculation applied."));
                    frm.set_value("custom_late_coming_minutes", 0);
                    frm.set_value("custom_early_going_minutes", 0);
                    frm.set_value("custom_late_early", 0);
                }
            }
        });
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
