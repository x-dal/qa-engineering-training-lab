export type Role='admin'|'staff'; export type OrderStatus='pending'|'paid'|'shipped'|'delivered'|'cancelled';
export interface User{id:number;email:string;full_name:string;role:Role;is_active:boolean;created_at:string;updated_at:string}
export interface Customer{id:number;name:string;email:string;phone:string;address:string;created_at:string;updated_at:string}
export interface Product{id:number;sku:string;name:string;description:string;price:string;stock_quantity:number;is_active:boolean;created_at:string;updated_at:string}
export interface OrderItem{id:number;product_id:number;quantity:number;unit_price:string;line_total:string;product:Product}
export interface Order{id:number;order_number:string;customer_id:number;status:OrderStatus;total_amount:string;created_by:number;created_at:string;updated_at:string;customer:Customer;items:OrderItem[]}
export interface Page<T>{items:T[];page:number;page_size:number;total:number;total_pages:number}
export interface Summary{customer_count:number;active_product_count:number;order_count:number;orders_by_status:{status:OrderStatus;count:number}[];low_stock_products:Product[];delivered_revenue:string}
