SELECT * FROM pharmacy_management.customerorderdetails;
ALTER TABLE customerorderdetails
ADD CONSTRAINT fk_cod_customer
    FOREIGN KEY (cid) REFERENCES customer(cid)
    ON UPDATE CASCADE ON DELETE SET NULL,
ADD CONSTRAINT fk_cod_order
    FOREIGN KEY (oid) REFERENCES orders(oid)
    ON UPDATE CASCADE ON DELETE SET NULL,
ADD CONSTRAINT fk_cod_medicine
    FOREIGN KEY (mid) REFERENCES medicine(mid)
    ON UPDATE CASCADE ON DELETE SET NULL;
